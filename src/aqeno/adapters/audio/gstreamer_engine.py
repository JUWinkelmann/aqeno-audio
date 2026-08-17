"""`AudioEngine` via GStreamer `playbin3` — ADR 0003, `src/aqeno/ports/audio.py`.

One `playbin3` element is built once and reused for the engine's lifetime. Files
and HTTP sources differ only in the resolved URI; `playbin3` handles demux,
decode and sink selection either way.

Threading: GStreamer's bus posts messages asynchronously. A dedicated background
thread polls the bus with a bounded timeout (`_BUS_POLL_INTERVAL`) and turns
messages into port-level `on_state` / `on_failure` / `on_finished` callbacks —
never `time.sleep()`, and no dependency on a GLib main loop existing anywhere
else in the process. Port callbacks therefore run on that background thread; a
caller that touches non-thread-safe state (a Qt view model, for instance) is
responsible for marshalling back to its own thread. That is an application-layer
concern, not this adapter's.

Gapless transitions use `playbin3`'s `about-to-finish` signal (ADR 0009 § 4a):
the handler sets the next URI directly on the still-playing pipeline, so the
transition never passes through `NULL`/`READY` and never produces an
end-of-stream for the chapter that just finished.
"""

# ruff: noqa: E402 -- Gst must be version-pinned before importing gi.repository.

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import cast

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst

from aqeno.adapters.audio.errors import SourceKind, map_bus_error
from aqeno.domain.content import LocalFileSource, Source
from aqeno.ports.audio import AudioCapabilities, AudioFailure, TransportState

logger = logging.getLogger(__name__)

_BUS_POLL_INTERVAL = 100 * Gst.MSECOND
"""Bounded wait per bus poll. Small enough that state/failure callbacks feel
immediate; the loop simply re-polls when nothing arrived, no sleep involved."""


def gain_for_volume(volume: int) -> float:
    """Logical 0-100 to linear pipeline gain — `CONFIGURATION_DEFAULTS.md` § 3.1.

    `gain = (v/100)**3`. Applied inside the pipeline, never the system mixer, so
    nothing outside AQENO can move a ceiling (ADR 0003, ADR 0006 § 6). Ceilings
    are enforced above this layer; this function does not clamp `volume`.
    """
    return (volume / 100) ** 3


def _source_kind(source: Source) -> SourceKind:
    return SourceKind.LOCAL_FILE if isinstance(source, LocalFileSource) else SourceKind.HTTP


def _source_to_uri(source: Source) -> str:
    if isinstance(source, LocalFileSource):
        return cast(str, Gst.filename_to_uri(str(Path(source.path).resolve())))
    return source.url


class GStreamerAudioEngine:
    """Implements `aqeno.ports.audio.AudioEngine` against `playbin3`.

    `audio_sink` lets a caller inject a specific sink element — `fakesink` so
    contract tests run without a real audio device, or a deliberately bogus ALSA
    device to provoke `AUDIO_DEVICE_MISSING` without hardware. Left `None`,
    `playbin3` picks its own sink (`autoaudiosink` by default), which is what the
    composition root uses for real playback.
    """

    def __init__(self, audio_sink: Gst.Element | None = None) -> None:
        Gst.init(None)

        self._pipeline = Gst.ElementFactory.make("playbin3", "aqeno-playbin")
        if self._pipeline is None:
            raise RuntimeError("GStreamer could not create a playbin3 element")
        if audio_sink is not None:
            self._pipeline.set_property("audio-sink", audio_sink)
        self._pipeline.connect("about-to-finish", self._on_about_to_finish)

        self._state = TransportState.IDLE
        self._capabilities: AudioCapabilities | None = None
        self._current_source: Source | None = None
        self._pending_gapless_source: Source | None = None
        self._awaiting_preroll = False
        self._stream_start_count = 0

        self._next_lock = threading.Lock()
        self._next_source: Source | None = None

        self._state_callback: Callable[[TransportState], None] | None = None
        self._failure_callback: Callable[[AudioFailure], None] | None = None
        self._source_changed_callback: Callable[[Source], None] | None = None
        self._finished_callback: Callable[[], None] | None = None

        self._stop_event = threading.Event()
        self._bus_thread = threading.Thread(
            target=self._run_bus_loop, name="aqeno-audio-bus", daemon=True
        )
        self._bus_thread.start()

    # -- lifecycle (adapter-only, not part of the port) -------------------------

    def close(self) -> None:
        """Tear the pipeline and bus thread down. Not part of `AudioEngine`;
        used by test fixtures and, later, the composition root's shutdown path."""
        self._stop_event.set()
        self._bus_thread.join(timeout=5)
        self._pipeline.set_state(Gst.State.NULL)

    # -- AudioEngine --------------------------------------------------------

    def load(self, source: Source) -> None:
        bus = self._pipeline.get_bus()
        bus.set_flushing(True)
        bus.set_flushing(False)

        self._pipeline.set_state(Gst.State.NULL)
        self._current_source = source
        self._pending_gapless_source = None
        self._capabilities = None
        self._awaiting_preroll = True
        self._stream_start_count = 0
        with self._next_lock:
            self._next_source = None

        self._pipeline.set_property("uri", _source_to_uri(source))
        self._set_state(TransportState.LOADING)
        self._pipeline.set_state(Gst.State.PAUSED)

    def play(self) -> None:
        self._pipeline.set_state(Gst.State.PLAYING)

    def pause(self) -> None:
        self._pipeline.set_state(Gst.State.PAUSED)

    def stop(self) -> None:
        bus = self._pipeline.get_bus()
        self._pipeline.set_state(Gst.State.NULL)
        bus.set_flushing(True)
        bus.set_flushing(False)
        self._capabilities = None
        self._current_source = None
        with self._next_lock:
            self._next_source = None
        self._set_state(TransportState.STOPPED)

    def seek(self, position: timedelta) -> None:
        if self._capabilities is None or not self._capabilities.seekable:
            return  # no-op on a non-seekable source, per the port contract
        self._pipeline.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            int(position.total_seconds() * Gst.SECOND),
        )

    def set_volume(self, volume: int) -> None:
        self._pipeline.set_property("volume", gain_for_volume(volume))

    @property
    def position(self) -> timedelta | None:
        ok, position_ns = self._pipeline.query_position(Gst.Format.TIME)
        if not ok or position_ns < 0:
            return None
        return timedelta(seconds=position_ns / Gst.SECOND)

    @property
    def state(self) -> TransportState:
        return self._state

    @property
    def capabilities(self) -> AudioCapabilities | None:
        return self._capabilities

    def prepare_next(self, source: Source | None) -> None:
        with self._next_lock:
            self._next_source = source

    def on_state(self, callback: Callable[[TransportState], None]) -> None:
        self._state_callback = callback

    def on_failure(self, callback: Callable[[AudioFailure], None]) -> None:
        self._failure_callback = callback

    def on_source_changed(self, callback: Callable[[Source], None]) -> None:
        self._source_changed_callback = callback

    def on_finished(self, callback: Callable[[], None]) -> None:
        self._finished_callback = callback

    # -- internals ------------------------------------------------------------

    def _set_state(self, state: TransportState) -> None:
        if state == self._state:
            return
        self._state = state
        if self._state_callback is not None:
            self._state_callback(state)

    def _query_capabilities(self) -> AudioCapabilities:
        ok, duration_ns = self._pipeline.query_duration(Gst.Format.TIME)
        duration = timedelta(seconds=duration_ns / Gst.SECOND) if ok and duration_ns >= 0 else None

        seek_query = Gst.Query.new_seeking(Gst.Format.TIME)
        seekable = False
        if self._pipeline.query(seek_query):
            seekable = seek_query.parse_seeking()[1]

        return AudioCapabilities(seekable=seekable, duration=duration)

    def _on_about_to_finish(self, playbin: Gst.Element) -> None:
        """Runs on GStreamer's own streaming thread (ADR 0009 § 4a).

        Setting `uri` here, synchronously and before returning, is what makes
        the transition gapless: `playbin3` swaps in the next URI without ever
        leaving `PLAYING`, so no `EOS` reaches the bus for the chapter that just
        finished.
        """
        with self._next_lock:
            next_source = self._next_source
            self._next_source = None
        if next_source is not None:
            playbin.set_property("uri", _source_to_uri(next_source))
            self._pending_gapless_source = next_source

    def _run_bus_loop(self) -> None:
        bus = self._pipeline.get_bus()
        message_types = (
            Gst.MessageType.ERROR
            | Gst.MessageType.EOS
            | Gst.MessageType.ASYNC_DONE
            | Gst.MessageType.STATE_CHANGED
            | Gst.MessageType.STREAM_START
        )
        while not self._stop_event.is_set():
            message = bus.timed_pop_filtered(_BUS_POLL_INTERVAL, message_types)
            if message is None:
                continue
            try:
                self._handle_message(message)
            except Exception:
                # A bug here must not silently stop state/failure reporting —
                # that would be exactly the "silent no-op" FAILURE_STATES.md
                # forbids. Log with the full traceback and keep polling.
                logger.exception("error while handling GStreamer bus message %s", message.type)

    def _handle_message(self, message: Gst.Message) -> None:
        if message.type == Gst.MessageType.ERROR:
            self._handle_error(message)
        elif message.type == Gst.MessageType.EOS:
            self._handle_eos()
        elif message.src == self._pipeline:
            if message.type == Gst.MessageType.ASYNC_DONE:
                self._handle_async_done()
            elif message.type == Gst.MessageType.STATE_CHANGED:
                self._handle_state_changed(message)
            elif message.type == Gst.MessageType.STREAM_START:
                self._handle_stream_start()

    def _handle_error(self, message: Gst.Message) -> None:
        gerror, debug = message.parse_error()
        source_kind = (
            _source_kind(self._current_source) if self._current_source else (SourceKind.LOCAL_FILE)
        )
        was_playing = self._state is TransportState.PLAYING
        failure = map_bus_error(gerror, debug, source_kind=source_kind, was_playing=was_playing)

        bus = self._pipeline.get_bus()
        self._pipeline.set_state(Gst.State.NULL)
        bus.set_flushing(True)
        bus.set_flushing(False)
        self._capabilities = None

        if self._failure_callback is not None:
            self._failure_callback(failure)
        self._set_state(TransportState.FAILED)

    def _handle_eos(self) -> None:
        # A next source is only ever still armed here if `about-to-finish` fired
        # too late to take effect — the ordinary gapless path clears
        # `_next_source` and switches the URI before EOS could ever be posted.
        bus = self._pipeline.get_bus()
        self._pipeline.set_state(Gst.State.NULL)
        bus.set_flushing(True)
        bus.set_flushing(False)
        self._capabilities = None
        self._current_source = None

        if self._finished_callback is not None:
            self._finished_callback()
        self._set_state(TransportState.STOPPED)

    def _handle_async_done(self) -> None:
        if not self._awaiting_preroll:
            return
        self._awaiting_preroll = False
        self._capabilities = self._query_capabilities()
        self._set_state(TransportState.PAUSED)

    def _handle_state_changed(self, message: Gst.Message) -> None:
        _old, new, pending = message.parse_state_changed()
        if pending != Gst.State.VOID_PENDING:
            return  # transition still in progress; wait for the settled state
        if new == Gst.State.PLAYING:
            self._set_state(TransportState.PLAYING)
        elif new == Gst.State.PAUSED and not self._awaiting_preroll:
            self._set_state(TransportState.PAUSED)

    def _handle_stream_start(self) -> None:
        self._stream_start_count += 1
        if self._stream_start_count == 1:
            return  # the initial load's own stream start; ASYNC_DONE covers it
        # A gapless transition just happened: playbin3 is now playing the source
        # armed in `_on_about_to_finish`. Refresh capabilities for the new
        # chapter without touching `_state` or firing any callback — this
        # boundary is a Group D event, invisible to state and display alike.
        if self._pending_gapless_source is not None:
            self._current_source = self._pending_gapless_source
            self._pending_gapless_source = None
        self._capabilities = self._query_capabilities()
        if self._current_source is not None and self._source_changed_callback is not None:
            self._source_changed_callback(self._current_source)
