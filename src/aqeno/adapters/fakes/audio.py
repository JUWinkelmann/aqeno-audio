"""Scriptable fake `AudioEngine` — ADR 0008 §§ 3, 8.

Implements `aqeno.ports.audio.AudioEngine` without GStreamer or an audio device,
so `application/` can be tested against it with GStreamer absent entirely. For
the `CONTENT`-class failures that can genuinely be told apart by looking at a
`LocalFileSource` on disk — missing, unreadable, unrecognised container — this
fake inspects the file the same way the real adapter's `load()` would discover
the problem, so the same generated fixture drives both engines in
`tests/contracts/test_audio.py`.

The failures a filesystem inspection cannot produce — a dropped stream, a lost
audio device — have no local equivalent to inspect, so this fake also exposes a
small scripting surface (`force_*` / `simulate_*`, all prefixed and none part of
`AudioEngine`) that lets a test drive it directly into any `TransportState` or
`FailureCode`.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

from aqeno.domain.content import HttpSource, LocalFileSource, Source
from aqeno.ports.audio import AudioCapabilities, AudioFailure, FailureCode, TransportState

_KNOWN_MAGIC: dict[bytes, str] = {
    b"RIFF": "wav",
    b"fLaC": "flac",
    b"OggS": "ogg",
    b"ID3": "mp3",
}
"""Enough to tell "recognisable container" from "not audio at all" — the same
distinction `playbin3`'s typefinder makes before `CODEC_UNSUPPORTED`."""

_MP3_FRAME_SYNC = b"\xff\xfb"


def _looks_like_a_recognised_container(data: bytes) -> bool:
    if data[:2] == _MP3_FRAME_SYNC:
        return True
    return any(data.startswith(magic) for magic in _KNOWN_MAGIC)


class FakeAudioEngine:
    """In-memory stand-in for `GStreamerAudioEngine`. No `gi`, no audio device."""

    def __init__(self) -> None:
        self._state = TransportState.IDLE
        self._capabilities: AudioCapabilities | None = None
        self._current_source: Source | None = None
        self._next_source: Source | None = None
        self._position: timedelta | None = None
        self.last_volume: int | None = None
        self.last_gain: float | None = None

        self._state_callback: Callable[[TransportState], None] | None = None
        self._failure_callback: Callable[[AudioFailure], None] | None = None
        self._source_changed_callback: Callable[[Source], None] | None = None
        self._finished_callback: Callable[[], None] | None = None

        self._forced_load_failure: AudioFailure | None = None
        self._forced_capabilities: AudioCapabilities | None = None

    # -- AudioEngine -----------------------------------------------------------

    def load(self, source: Source) -> None:
        self._current_source = source
        self._capabilities = None
        self._position = None
        self._set_state(TransportState.LOADING)

        failure = self._forced_load_failure or self._inspect(source)
        self._forced_load_failure = None
        if failure is not None:
            self._current_source = None
            if self._failure_callback is not None:
                self._failure_callback(failure)
            self._set_state(TransportState.FAILED)
            return

        if self._forced_capabilities is not None:
            self._capabilities = self._forced_capabilities
            self._forced_capabilities = None
        elif isinstance(source, HttpSource):
            self._capabilities = AudioCapabilities(seekable=source.seekable, duration=None)
        else:
            self._capabilities = AudioCapabilities(seekable=True, duration=None)
        self._position = timedelta(0)
        self._set_state(TransportState.PAUSED)

    def play(self) -> None:
        if self._state in (TransportState.PAUSED, TransportState.STOPPED):
            if self._position is None:
                self._position = timedelta(0)
            self._set_state(TransportState.PLAYING)

    def pause(self) -> None:
        if self._state is TransportState.PLAYING:
            self._set_state(TransportState.PAUSED)

    def stop(self) -> None:
        self._capabilities = None
        self._current_source = None
        self._next_source = None
        self._position = None
        self._set_state(TransportState.STOPPED)

    def seek(self, position: timedelta) -> None:
        if self._capabilities is None or not self._capabilities.seekable:
            return  # no-op on a non-seekable source, per the port contract
        self._position = position

    def set_volume(self, volume: int) -> None:
        self.last_volume = volume
        self.last_gain = (volume / 100) ** 3

    @property
    def position(self) -> timedelta | None:
        return self._position

    @property
    def state(self) -> TransportState:
        return self._state

    @property
    def capabilities(self) -> AudioCapabilities | None:
        return self._capabilities

    def prepare_next(self, source: Source | None) -> None:
        self._next_source = source

    def on_state(self, callback: Callable[[TransportState], None]) -> None:
        self._state_callback = callback

    def on_failure(self, callback: Callable[[AudioFailure], None]) -> None:
        self._failure_callback = callback

    def on_source_changed(self, callback: Callable[[Source], None]) -> None:
        self._source_changed_callback = callback

    def on_finished(self, callback: Callable[[], None]) -> None:
        self._finished_callback = callback

    # -- scripting surface, not part of AudioEngine -----------------------------

    def force_next_load_failure(self, code: FailureCode, detail: str = "scripted") -> None:
        """The next `load()` call fails with `code` regardless of the source."""
        self._forced_load_failure = AudioFailure(code=code, detail=detail)

    def force_next_capabilities(self, capabilities: AudioCapabilities) -> None:
        """The next successful `load()` reports `capabilities` verbatim."""
        self._forced_capabilities = capabilities

    def simulate_mid_playback_failure(self, code: FailureCode, detail: str = "scripted") -> None:
        """A failure that only makes sense once playback has started —
        `STREAM_INTERRUPTED`, `AUDIO_DEVICE_LOST` — with no filesystem
        equivalent for `load()` to discover."""
        self._capabilities = None
        if self._failure_callback is not None:
            self._failure_callback(AudioFailure(code=code, detail=detail))
        self._set_state(TransportState.FAILED)

    def simulate_finished(self) -> None:
        """The loaded source reaches its end.

        Mirrors `GStreamerAudioEngine`'s EOS/`about-to-finish` split: if
        `prepare_next` armed a source, this is a gapless transition — playback
        continues, `_state` is untouched, and `on_finished` does not fire.
        Otherwise this is exactly what `on_finished` documents.
        """
        if self._next_source is not None:
            self._current_source = self._next_source
            self._next_source = None
            if self._forced_capabilities is not None:
                self._capabilities = self._forced_capabilities
                self._forced_capabilities = None
            if self._source_changed_callback is not None:
                self._source_changed_callback(self._current_source)
            return
        self._capabilities = None
        self._current_source = None
        if self._finished_callback is not None:
            self._finished_callback()
        self._set_state(TransportState.STOPPED)

    # -- internals ---------------------------------------------------------

    def _set_state(self, state: TransportState) -> None:
        if state == self._state:
            return
        self._state = state
        if self._state_callback is not None:
            self._state_callback(state)

    def _inspect(self, source: Source) -> AudioFailure | None:
        """Best-effort mirror of what `playbin3` would discover for a
        `LocalFileSource` without actually decoding it. `HttpSource` has
        nothing to inspect locally, so it always succeeds here — network
        failures are scripted (`force_next_load_failure`), same as on the real
        adapter they come from a live connection, not a file."""
        if not isinstance(source, LocalFileSource):
            return None
        path = Path(source.path)
        if not path.exists():
            return AudioFailure(code=FailureCode.SOURCE_MISSING, detail=f"no such file: {path}")
        if not path.is_file():
            return AudioFailure(code=FailureCode.SOURCE_MISSING, detail=f"not a file: {path}")
        try:
            with path.open("rb") as handle:
                header = handle.read(16)
        except PermissionError:
            return AudioFailure(
                code=FailureCode.SOURCE_UNREADABLE, detail=f"permission denied: {path}"
            )
        if not _looks_like_a_recognised_container(header):
            return AudioFailure(
                code=FailureCode.CODEC_UNSUPPORTED, detail=f"unrecognised container: {path}"
            )
        return None
