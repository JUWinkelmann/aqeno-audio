"""AQENO process entry point and adapter composition root."""

from __future__ import annotations

import argparse
import logging
import threading
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol, runtime_checkable

from aqeno.adapters.clock import SystemClock
from aqeno.adapters.fakes.audio import FakeAudioEngine
from aqeno.adapters.input.keyboard import KeyboardSimulator
from aqeno.adapters.metadata import MutagenProbe
from aqeno.adapters.persistence.sqlite_library import SqliteLibrary, open_library
from aqeno.adapters.persistence.toml_settings import TomlSettingsStore
from aqeno.application.ingestion import run_scan
from aqeno.application.playback import PlaybackSession
from aqeno.config.defaults import Settings
from aqeno.config.paths import artwork_dir
from aqeno.domain.profile import (
    DisplayPolicy,
    ExperienceLevel,
    Profile,
    Role,
    VolumeLimits,
)
from aqeno.ports.audio import AudioEngine

logger = logging.getLogger(__name__)


@runtime_checkable
class _Closable(Protocol):
    def close(self) -> None: ...


@dataclass(slots=True)
class AqenoProcess:
    """Resources owned by one running AQENO process."""

    session: PlaybackSession
    library: SqliteLibrary
    inputs: KeyboardSimulator
    audio: AudioEngine
    scan_thread: threading.Thread | None = None
    """The content scan (ADR 0014 § 5). Started off this thread so it never
    blocks startup; joined here so shutdown never closes the library out from
    under a write still in flight."""

    def close(self) -> None:
        if self.scan_thread is not None:
            self.scan_thread.join()
        try:
            self.session.shutdown()
        finally:
            try:
                if isinstance(self.audio, _Closable):
                    self.audio.close()
            finally:
                self.library.close()


def _kids_early_profile(settings: Settings) -> Profile:
    return Profile(
        name="kids-early",
        level=ExperienceLevel.KIDS_EARLY,
        role=Role.USER,
        display=DisplayPolicy(
            inactivity_timeout=timedelta(seconds=settings.display.kids_early),
            night_timeout=timedelta(seconds=settings.display.night_override),
            allows_dim=False,
            dim_hold=None,
            interactive_brightness=settings.brightness.interactive_kids_early,
            dim_brightness=0,
            ambient_brightness=settings.brightness.ambient_kids_early,
            night_brightness=settings.brightness.night_minimum,
            led_brightness=settings.brightness.led_normal,
        ),
        volume=VolumeLimits(
            maximum=settings.volume.child_maximum,
            night_maximum=settings.volume.night_ceiling,
            headphone_maximum=settings.volume.headphone_maximum,
        ),
    )


def _audio_engine(fake_hardware: frozenset[str]) -> AudioEngine:
    if "all" in fake_hardware or "audio" in fake_hardware:
        return FakeAudioEngine()

    from aqeno.adapters.audio.gstreamer_engine import GStreamerAudioEngine

    return GStreamerAudioEngine()


def _run_startup_scan(library: SqliteLibrary, settings: Settings) -> None:
    """Runs on its own thread (ADR 0014 § 5: never the playback/input thread).

    Any failure here is a `DEVICE`-class problem (`FAILURE_STATES.md`) — the
    scan's own file-level failures are already handled inside `run_scan()`;
    this guard is only for something unexpected, and it must never take the
    rest of the process down with it.
    """
    try:
        summary = run_scan(
            library=library,
            probe=MutagenProbe(),
            clock=SystemClock(),
            roots=settings.library.roots,
            follow_symlinks=settings.library.follow_symlinks,
            artwork_dir=artwork_dir(),
        )
        logger.info(
            "content scan complete",
            extra={
                "candidates_seen": summary.candidates_seen,
                "works_touched": summary.works_touched,
                "works_marked_unavailable": summary.works_marked_unavailable,
            },
        )
    except Exception:
        logger.exception("content scan failed")


def _open_process(*, profile_name: str, fake_hardware: frozenset[str]) -> AqenoProcess:
    settings = TomlSettingsStore().load()
    library = open_library()
    audio: AudioEngine | None = None
    scan_thread: threading.Thread | None = None
    try:
        profile = library.get_profile(profile_name)
        if profile is None:
            if profile_name != "kids-early":
                raise ValueError(f"profile {profile_name!r} does not exist")
            profile = _kids_early_profile(settings)
            library.save_profile(profile)

        # LOCAL_READY: the database is open and the profile is resolved.
        # Scanning off this thread means it never blocks PLAYBACK_READY below.
        if settings.library.scan_on_startup:
            scan_thread = threading.Thread(
                target=_run_startup_scan,
                args=(library, settings),
                name="aqeno-content-scan",
                daemon=True,
            )
            scan_thread.start()

        inputs = KeyboardSimulator()
        audio = _audio_engine(fake_hardware)
        session = PlaybackSession(
            audio=audio,
            library=library,
            clock=SystemClock(),
            settings=settings,
            inputs=inputs,
        )
        session.use_profile(profile)
    except BaseException:
        if scan_thread is not None:
            scan_thread.join()
        if isinstance(audio, _Closable):
            audio.close()
        library.close()
        raise

    logger.info(
        "AQENO local core ready",
        extra={"profile": profile.name, "content_count": len(library.list_content())},
    )
    return AqenoProcess(
        session=session, library=library, inputs=inputs, audio=audio, scan_thread=scan_thread
    )


def _fake_hardware(value: str | None) -> frozenset[str]:
    if value is None or value == "all":
        return frozenset({"all"})
    parts = frozenset(part.strip() for part in value.split(",") if part.strip())
    allowed = {"audio", "display", "input", "nfc"}
    unknown = parts - allowed
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown fake hardware: {', '.join(sorted(unknown))}")
    return parts


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aqeno")
    parser.add_argument("--profile", default="kids-early")
    parser.add_argument(
        "--fake-hardware",
        nargs="?",
        const="all",
        type=_fake_hardware,
        help="fake all hardware, or a comma-separated subset",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="open and close the local core once, then exit",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.fake_hardware is None or not ({"all", "input"} & args.fake_hardware):
        _parser().error(
            "Reference Hardware input adapters are not implemented yet; "
            "include input in --fake-hardware"
        )

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        process = _open_process(profile_name=args.profile, fake_hardware=args.fake_hardware)
    except Exception as exc:
        logger.error("AQENO could not start: %s", exc)
        return 1

    try:
        if not args.check:
            logger.info("Device UI is not implemented yet; press Ctrl+C to stop")
            threading.Event().wait()
    except KeyboardInterrupt:
        logger.info("AQENO stopping")
    finally:
        process.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
