"""Cross-boundary scenarios for the First Vertical Slice.

These tests intentionally wire the real application services together and keep
the hardware at deterministic fakes.  The unit suites already prove individual
state machines and adapters; this file protects the user-visible seams where
selection, launch, persistence, display policy and audio must remain separate.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from aqeno.adapters.fakes import (
    FakeAudioEngine,
    FakeClock,
    FakeDisplayPanel,
    FakeInputBus,
    FakeLibrary,
    FakeStatusLeds,
)
from aqeno.adapters.input import KeyboardSimulator
from aqeno.adapters.persistence import open_library
from aqeno.application.device_ui import DeviceSurface, DeviceUiState
from aqeno.application.display import DisplayService
from aqeno.application.playback import PlaybackSession
from aqeno.application.readiness import Readiness, ReadinessState
from aqeno.config.defaults import default_settings
from aqeno.domain.content import ContentId, ContentItem, ContentKind, LocalFileSource
from aqeno.domain.display import DisplayState
from aqeno.domain.profile import DisplayPolicy, ExperienceLevel, Profile, Role, VolumeLimits
from aqeno.ports.audio import TransportState
from aqeno.ports.input import TogglePlayback, VolumeDelta


def _profile(*, inactivity: int = 30, dim_hold: int = 10) -> Profile:
    return Profile(
        name="kids-early",
        level=ExperienceLevel.KIDS_EARLY,
        role=Role.USER,
        display=DisplayPolicy(
            inactivity_timeout=timedelta(seconds=inactivity),
            night_timeout=timedelta(seconds=10),
            allows_dim=True,
            dim_hold=timedelta(seconds=dim_hold),
            interactive_brightness=70,
            dim_brightness=8,
            ambient_brightness=40,
            night_brightness=5,
            led_brightness=20,
        ),
        volume=VolumeLimits(maximum=70, night_maximum=35, headphone_maximum=55),
    )


def _local_item(tmp_path: Path, title: str) -> ContentItem:
    """A minimal container header is enough for the fake audio contract."""
    source = tmp_path / f"{title.lower().replace(' ', '-')}.wav"
    source.write_bytes(b"RIFF" + b"\x00" * 32)
    return ContentItem(
        id=ContentId(),
        title=title,
        kind=ContentKind.AUDIOBOOK,
        sources=(LocalFileSource(source),),
        duration=timedelta(minutes=5),
        artwork=source.with_suffix(".jpg"),
    )


def _wired_core(
    *,
    library: FakeLibrary,
    item_profile: Profile | None = None,
    panel: FakeDisplayPanel | None = None,
    inputs: FakeInputBus | KeyboardSimulator | None = None,
) -> tuple[
    FakeClock,
    FakeAudioEngine,
    FakeInputBus | KeyboardSimulator,
    PlaybackSession,
    DisplayService,
    DeviceUiState,
]:
    clock = FakeClock()
    input_bus = inputs if inputs is not None else FakeInputBus()
    audio = FakeAudioEngine()
    profile = item_profile or _profile()
    session = PlaybackSession(
        audio=audio,
        library=library,
        clock=clock,
        settings=default_settings(),
        inputs=input_bus,
    )
    session.use_profile(profile)

    readiness = Readiness(clock)
    readiness.advance(ReadinessState.LOCAL_READY)
    readiness.advance(ReadinessState.PLAYBACK_READY)
    readiness.advance(ReadinessState.UI_READY)
    display = DisplayService(
        panel=panel or FakeDisplayPanel(),
        leds=FakeStatusLeds(),
        clock=clock,
        readiness=readiness,
        profile=profile,
        settings=default_settings(),
    )
    session.on_changed(display.handle_playback_changed)
    input_bus.on_input(display.handle_input)
    ui = DeviceUiState(library=library, playback=session, display=display, profile=profile)
    return clock, audio, input_bus, session, display, ui


def test_local_tiles_and_simulated_nfc_launch_share_the_playback_path(tmp_path: Path) -> None:
    """Kids selection and the simulator's NFC UID both launch local audio."""
    library = FakeLibrary()
    first, second, third = (_local_item(tmp_path, name) for name in ("One", "Two", "Three"))
    for item in (first, second, third):
        library.save_content(item)

    simulator = KeyboardSimulator()
    _, audio, _, session, _, ui = _wired_core(library=library, inputs=simulator)
    ui.refresh_library()

    assert ui.snapshot.surface is DeviceSurface.HOME
    assert tuple(tile.content_id for tile in ui.snapshot.tiles) == (
        first.id,
        third.id,
        second.id,
    )
    assert all(tile.artwork is not None for tile in ui.snapshot.tiles)

    assert ui.select_content(first.id)
    assert session.item == first
    assert audio.state is TransportState.PLAYING

    library.map_tag("AQENO-TEST-2", second.id)
    assert simulator.handle_key("2")
    assert session.item == second
    assert audio.state is TransportState.PLAYING


def test_local_resume_survives_a_new_sqlite_library_and_session(tmp_path: Path) -> None:
    """A restart must resume from durable local state without any network rung."""
    data_dir = tmp_path / "data"
    media = _local_item(tmp_path, "Restart Story")
    profile = _profile()

    first_library = open_library(data_dir)
    first_inputs = FakeInputBus()
    first_audio = FakeAudioEngine()
    first_clock = FakeClock()
    first_library.save_content(media)
    first_session = PlaybackSession(
        audio=first_audio,
        library=first_library,
        clock=first_clock,
        settings=default_settings(),
        inputs=first_inputs,
    )
    first_session.use_profile(profile)
    first_session.start(media, profile)
    assert first_audio.state is TransportState.PLAYING
    first_audio.seek(timedelta(seconds=42))
    first_inputs.emit(TogglePlayback())
    first_session.shutdown()
    first_library.close()

    restarted_library = open_library(data_dir)
    restarted_session: PlaybackSession | None = None
    try:
        restarted_inputs = FakeInputBus()
        restarted_audio = FakeAudioEngine()
        restarted_session = PlaybackSession(
            audio=restarted_audio,
            library=restarted_library,
            clock=FakeClock(),
            settings=default_settings(),
            inputs=restarted_inputs,
        )
        restarted_session.use_profile(profile)
        resumed_item = restarted_library.get_content(media.id)
        assert resumed_item is not None
        restarted_session.start(resumed_item, profile)

        assert restarted_audio.state is TransportState.PLAYING
        assert restarted_audio.position == timedelta(seconds=39)
    finally:
        if restarted_session is not None:
            restarted_session.shutdown()
        restarted_library.close()


def test_simulated_wake_restores_interactive_without_affecting_audio(tmp_path: Path) -> None:
    library = FakeLibrary()
    item = _local_item(tmp_path, "Wake Story")
    library.save_content(item)
    simulator = KeyboardSimulator()
    _, audio, _, session, display, _ = _wired_core(library=library, inputs=simulator)

    session.start(item, _profile())
    assert display.snapshot.state is DisplayState.OFF
    assert simulator.handle_key("w")

    assert display.snapshot.state is DisplayState.INTERACTIVE
    assert audio.state is TransportState.PLAYING


def test_display_panel_failure_leaves_local_playback_and_controls_usable(tmp_path: Path) -> None:
    """The optional visual path may fail without taking down the audio path."""

    class FailingPanel(FakeDisplayPanel):
        def set_power(self, on: bool) -> None:
            raise OSError("panel unavailable")

    library = FakeLibrary()
    item = _local_item(tmp_path, "Headless Story")
    library.save_content(item)
    clock, audio, inputs, session, display, _ = _wired_core(library=library, panel=FailingPanel())

    assert display.snapshot.state is DisplayState.OFF
    session.start(item, _profile())
    assert audio.state is TransportState.PLAYING

    volume_before = session.volume
    inputs.emit(TogglePlayback())
    assert audio.state is TransportState.PAUSED
    inputs.emit(TogglePlayback())
    inputs.emit(VolumeDelta(1))

    assert audio.state is TransportState.PLAYING
    assert session.volume > volume_before
    assert display.snapshot.state is DisplayState.OFF
    assert clock.pending >= 1
