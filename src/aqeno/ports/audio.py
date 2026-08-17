"""Audio port — ADR 0003, `PLATFORM_CONTRACTS.md` § Audio contract.

Engine-agnostic. No GStreamer type, and no GStreamer message text, crosses this
boundary: `docs/implementation/FAILURE_STATES.md` names this as the boundary at which
technical language would otherwise leak towards a child-facing UI.

The engine loads, plays, pauses, seeks and reports. It owns no queue, no
next/previous logic and no display behaviour — those sit above it.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum, auto
from typing import Protocol

from aqeno.domain.content import Source


class TransportState(StrEnum):
    IDLE = auto()
    LOADING = auto()
    PLAYING = auto()
    PAUSED = auto()
    STOPPED = auto()
    FAILED = auto()


class FailureCode(StrEnum):
    """The stable codes from FAILURE_STATES.md § Failure codes.

    The adapter maps every engine error onto one of these. The UI and the logs depend
    on the code, never on a message string.
    """

    SOURCE_MISSING = auto()
    SOURCE_UNREADABLE = auto()
    CODEC_UNSUPPORTED = auto()
    STREAM_UNREACHABLE = auto()
    STREAM_INTERRUPTED = auto()
    DECODE_FAILED = auto()
    AUDIO_DEVICE_MISSING = auto()
    AUDIO_DEVICE_LOST = auto()


class FailureClass(StrEnum):
    """FAILURE_STATES.md § Severity classes."""

    TRANSIENT = auto()
    CONTENT = auto()
    DEVICE = auto()


_FAILURE_CLASSES: dict[FailureCode, FailureClass] = {
    FailureCode.SOURCE_MISSING: FailureClass.CONTENT,
    FailureCode.SOURCE_UNREADABLE: FailureClass.CONTENT,
    FailureCode.CODEC_UNSUPPORTED: FailureClass.CONTENT,
    FailureCode.STREAM_UNREACHABLE: FailureClass.CONTENT,
    FailureCode.STREAM_INTERRUPTED: FailureClass.TRANSIENT,
    FailureCode.DECODE_FAILED: FailureClass.CONTENT,
    FailureCode.AUDIO_DEVICE_MISSING: FailureClass.DEVICE,
    FailureCode.AUDIO_DEVICE_LOST: FailureClass.DEVICE,
}


def classify(code: FailureCode) -> FailureClass:
    return _FAILURE_CLASSES[code]


@dataclass(frozen=True, slots=True)
class AudioFailure:
    code: FailureCode
    detail: str
    """Technical detail. For logs and the Manager surface only — never a child-facing
    surface, never spoken, never on a tile (FAILURE_STATES.md rule 5)."""
    position: timedelta | None = None

    @property
    def failure_class(self) -> FailureClass:
        return classify(self.code)


@dataclass(frozen=True, slots=True)
class AudioCapabilities:
    """Reported per loaded source, so the application can treat "radio has no resume
    position" as a domain fact rather than discovering it as a failure (ADR 0003)."""

    seekable: bool
    duration: timedelta | None


class AudioEngine(Protocol):
    """Playback of one source at a time.

    Nothing here may wake, dim or otherwise touch the display: every callback below
    corresponds to a Group D event, which produces no display transition in any state
    (`DISPLAY_STATE_MACHINE.md` invariant 2).
    """

    def load(self, source: Source) -> None:
        """Prepare a source. Reports through `on_state` and `on_failure`, not by raising."""
        ...

    def play(self) -> None: ...

    def pause(self) -> None: ...

    def stop(self) -> None: ...

    def seek(self, position: timedelta) -> None:
        """No-op where the loaded source is not seekable."""
        ...

    def set_volume(self, volume: int) -> None:
        """Logical 0-100, applied inside the pipeline rather than to the system mixer,
        so nothing outside AQENO can move a ceiling (ADR 0003, ADR 0006 § 6)."""
        ...

    @property
    def position(self) -> timedelta | None: ...

    @property
    def state(self) -> TransportState: ...

    @property
    def capabilities(self) -> AudioCapabilities | None: ...

    def prepare_next(self, source: Source | None) -> None:
        """Queue the next chapter for a gapless transition, or clear it with `None`.

        Required, not a refinement: a Hörspiel ripped from CD is continuous audio cut at
        arbitrary track points, so a gap at a chapter boundary lands mid-scene
        (ADR 0009 § 4a). The naive wait-for-end-then-load approach produces exactly that
        gap.
        """
        ...

    def on_state(self, callback: Callable[[TransportState], None]) -> None: ...

    def on_failure(self, callback: Callable[[AudioFailure], None]) -> None: ...

    def on_source_changed(self, callback: Callable[[Source], None]) -> None:
        """A source prepared for gapless playback became active."""
        ...

    def on_finished(self, callback: Callable[[], None]) -> None:
        """The loaded source reached its end and no prepared next source took over."""
        ...
