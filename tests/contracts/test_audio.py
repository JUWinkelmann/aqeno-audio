"""Contract suite for the audio port — ADR 0003, ADR 0008 §§ 3, 7.

Runs against both implementations of `AudioEngine`: the real
`GStreamerAudioEngine` (always with `fakesink`, so no audio device or Reference
hardware is needed) and `FakeAudioEngine`. `AUDIO_DEVICE_MISSING` also runs for
real, provoked with a deliberately nonexistent ALSA device rather than
`fakesink` — still no hardware required. Only `AUDIO_DEVICE_LOST` (a healthy
device disappearing mid-stream) has no software-only way to provoke against a
real sink and is `@pytest.mark.hardware`.

Fixture audio is generated with GStreamer at test time (ADR 0008 § 7): no audio
file is committed to the repository.
"""

# ruff: noqa: E402 -- Gst must be version-pinned before importing gi.repository.

from __future__ import annotations

import http.server
import os
import socket
import socketserver
import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import gi
import pytest

gi.require_version("Gst", "1.0")
from gi.repository import Gst

from aqeno.adapters.audio import GStreamerAudioEngine, gain_for_volume
from aqeno.adapters.fakes.audio import FakeAudioEngine
from aqeno.domain.content import HttpSource, LocalFileSource, Source
from aqeno.ports.audio import (
    AudioCapabilities,
    AudioEngine,
    AudioFailure,
    FailureClass,
    FailureCode,
    TransportState,
)

Gst.init(None)


# ---------------------------------------------------------------------------
# Fixture audio, generated with GStreamer at test time (ADR 0008 § 7).
# ---------------------------------------------------------------------------


def _render(path: Path, *, wave: str, seconds: int, encoder: str, freq: int | None = None) -> Path:
    """Render `seconds` of `wave` to `path` with a throwaway GStreamer pipeline,
    waiting on its own bus for `EOS` with a generous bounded timeout — no
    `time.sleep()`."""
    freq_part = f" freq={freq}" if freq is not None else ""
    description = (
        f"audiotestsrc wave={wave}{freq_part} samplesperbuffer=44100 num-buffers={seconds} "
        f"! audioconvert ! audio/x-raw,rate=44100 ! {encoder} ! filesink location={path}"
    )
    pipeline = Gst.parse_launch(description)
    pipeline.set_state(Gst.State.PLAYING)
    bus = pipeline.get_bus()
    message = bus.timed_pop_filtered(15 * Gst.SECOND, Gst.MessageType.EOS | Gst.MessageType.ERROR)
    pipeline.set_state(Gst.State.NULL)
    if message is None:
        raise RuntimeError(f"timed out rendering fixture {path}")
    if message.type == Gst.MessageType.ERROR:
        raise RuntimeError(f"failed to render fixture {path}: {message.parse_error()}")
    return path


@dataclass(frozen=True)
class AudioFixtures:
    valid: Path
    """~2s sine tone, FLAC. A generic "plays fine, has a known duration"
    source."""
    gapless_first: Path
    """Same file as `valid` — the first half of a gapless pair."""
    gapless_second: Path
    """~2s silence, WAV — a *different* container from `gapless_first`, so a
    dropped/duplicated buffer at the boundary would be more, not less,
    detectable."""
    missing: Path
    """Does not exist."""
    unreadable: Path
    """Exists, `chmod 000`."""
    codec_unsupported: Path
    """Exists, is not audio at all — `playbin3`'s typefinder cannot place it,
    the same as an exotic or DRM-protected container would produce."""
    corrupt: Path
    """A valid Ogg/Vorbis file with its middle third bit-flipped: header and
    footer intact, so it is found and typefound, but decoding it fails
    (`Gst.StreamError.DECODE`) — verified empirically; truncating instead of
    corrupting turned out not to trigger an error at all, since GStreamer's
    decoders are lenient about running out of data at a clean EOF."""
    stream_payload: bytes
    """Raw bytes of a ~5s FLAC file, served by the local HTTP fixtures used
    for `STREAM_INTERRUPTED`."""


@pytest.fixture(scope="session")
def audio_fixtures(tmp_path_factory: pytest.TempPathFactory) -> AudioFixtures:
    root = tmp_path_factory.mktemp("audio-fixtures")

    valid = _render(root / "valid.flac", wave="sine", seconds=2, encoder="flacenc", freq=440)
    gapless_second = _render(
        root / "gapless_second.wav", wave="silence", seconds=2, encoder="wavenc"
    )

    missing = root / "missing.flac"

    unreadable = _render(root / "unreadable.wav", wave="silence", seconds=1, encoder="wavenc")
    unreadable.chmod(0o000)

    codec_unsupported = root / "codec_unsupported.mp3"
    codec_unsupported.write_bytes(b"this is definitely not an audio file. " * 50)

    corrupt_source = _render(
        root / "corrupt_source.ogg", wave="sine", seconds=2, encoder="vorbisenc ! oggmux", freq=880
    )
    corrupt_bytes = bytearray(corrupt_source.read_bytes())
    n = len(corrupt_bytes)
    for i in range(n // 3, 2 * n // 3):
        corrupt_bytes[i] ^= 0xAA
    corrupt = root / "corrupt.ogg"
    corrupt.write_bytes(bytes(corrupt_bytes))

    stream_source = _render(
        root / "stream.flac", wave="sine", seconds=5, encoder="flacenc", freq=220
    )

    return AudioFixtures(
        valid=valid,
        gapless_first=valid,
        gapless_second=gapless_second,
        missing=missing,
        unreadable=unreadable,
        codec_unsupported=codec_unsupported,
        corrupt=corrupt,
        stream_payload=stream_source.read_bytes(),
    )


# ---------------------------------------------------------------------------
# Recorder and engine construction shared by every test below.
# ---------------------------------------------------------------------------


class Recorder:
    """Collects every port callback and waits for a predicate to become true,
    bounded by a real timeout — never `time.sleep()`. The fake fires
    callbacks synchronously (the wait returns immediately); the real engine
    fires from its background bus thread (the wait blocks on a
    `threading.Event` until it does, or fails loudly with everything
    observed so far)."""

    def __init__(self, engine: AudioEngine) -> None:
        self.states: list[TransportState] = []
        self.failures: list[AudioFailure] = []
        self.source_changes: list[Source] = []
        self.finished_count = 0
        self._event = threading.Event()
        engine.on_state(self._on_state)
        engine.on_failure(self._on_failure)
        engine.on_source_changed(self._on_source_changed)
        engine.on_finished(self._on_finished)

    def _on_state(self, state: TransportState) -> None:
        self.states.append(state)
        self._event.set()

    def _on_failure(self, failure: AudioFailure) -> None:
        self.failures.append(failure)
        self._event.set()

    def _on_source_changed(self, source: Source) -> None:
        self.source_changes.append(source)
        self._event.set()

    def _on_finished(self) -> None:
        self.finished_count += 1
        self._event.set()

    def wait_until(self, predicate: Callable[[], bool], timeout: float = 6.0) -> None:
        deadline = time.monotonic() + timeout
        while not predicate():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AssertionError(
                    f"condition not met within {timeout}s; states={self.states} "
                    f"failures={self.failures} finished_count={self.finished_count}"
                )
            self._event.wait(timeout=min(0.1, remaining))
            self._event.clear()


def _fakesink() -> Gst.Element:
    """`sync=True` so the pipeline is paced by the clock like a real sink —
    required for the gapless test to exercise real timing, and harmless
    (just a little slower) for everything else."""
    sink = Gst.ElementFactory.make("fakesink", None)
    sink.set_property("sync", True)
    return sink


def _make_engine(impl: str, *, audio_sink: Gst.Element | None = None) -> AudioEngine:
    if impl == "fake":
        return FakeAudioEngine()
    return GStreamerAudioEngine(audio_sink=audio_sink or _fakesink())


def _close_engine(engine: AudioEngine) -> None:
    if isinstance(engine, GStreamerAudioEngine):
        engine.close()


@pytest.fixture(params=["fake", "real"])
def engine(request: pytest.FixtureRequest) -> Iterator[AudioEngine]:
    made = _make_engine(request.param)
    yield made
    _close_engine(made)


# ---------------------------------------------------------------------------
# Transport states
# ---------------------------------------------------------------------------


class TestTransportStates:
    def test_idle_before_any_load(self, engine: AudioEngine) -> None:
        assert engine.state == TransportState.IDLE
        assert engine.capabilities is None
        assert engine.position is None

    def test_load_reaches_paused_via_loading(
        self, engine: AudioEngine, audio_fixtures: AudioFixtures
    ) -> None:
        recorder = Recorder(engine)
        engine.load(LocalFileSource(path=audio_fixtures.valid))
        recorder.wait_until(lambda: engine.state == TransportState.PAUSED)
        assert recorder.states[0] == TransportState.LOADING
        assert engine.capabilities is not None

    def test_play_pause_stop_cycle(
        self, engine: AudioEngine, audio_fixtures: AudioFixtures
    ) -> None:
        recorder = Recorder(engine)
        engine.load(LocalFileSource(path=audio_fixtures.valid))
        recorder.wait_until(lambda: engine.state == TransportState.PAUSED)

        engine.play()
        recorder.wait_until(lambda: engine.state == TransportState.PLAYING)

        engine.pause()
        recorder.wait_until(lambda: engine.state == TransportState.PAUSED)

        engine.stop()
        recorder.wait_until(lambda: engine.state == TransportState.STOPPED)
        assert engine.capabilities is None
        assert engine.position is None

    def test_on_finished_fires_when_nothing_prepared(
        self, engine: AudioEngine, audio_fixtures: AudioFixtures
    ) -> None:
        recorder = Recorder(engine)
        engine.load(LocalFileSource(path=audio_fixtures.gapless_first))
        recorder.wait_until(lambda: engine.state == TransportState.PAUSED)
        engine.play()
        recorder.wait_until(lambda: engine.state == TransportState.PLAYING)

        if isinstance(engine, FakeAudioEngine):
            engine.simulate_finished()
        else:
            recorder.wait_until(lambda: engine.state == TransportState.STOPPED, timeout=8)

        assert recorder.finished_count == 1
        assert recorder.source_changes == []
        assert engine.state == TransportState.STOPPED


# ---------------------------------------------------------------------------
# Capabilities
# ---------------------------------------------------------------------------


class TestCapabilities:
    def test_known_length_file_reports_duration_and_seekable(
        self, engine: AudioEngine, audio_fixtures: AudioFixtures
    ) -> None:
        recorder = Recorder(engine)
        if isinstance(engine, FakeAudioEngine):
            engine.force_next_capabilities(
                AudioCapabilities(seekable=True, duration=timedelta(seconds=2))
            )
        engine.load(LocalFileSource(path=audio_fixtures.valid))
        recorder.wait_until(lambda: engine.state == TransportState.PAUSED)

        capabilities = engine.capabilities
        assert capabilities is not None
        assert capabilities.seekable is True
        assert capabilities.duration is not None
        assert abs(capabilities.duration.total_seconds() - 2.0) < 0.2


# ---------------------------------------------------------------------------
# Seek
# ---------------------------------------------------------------------------


class TestSeek:
    def test_seek_is_noop_when_not_seekable(self) -> None:
        """Only exercised against the fake: constructing a genuinely
        non-seekable *and* reliably loadable real source (a live stream
        without Range support) is heavier machinery than this no-op rule
        needs to be trusted — the rule itself is engine-agnostic logic that
        both implementations share verbatim."""
        engine = FakeAudioEngine()
        engine.force_next_capabilities(AudioCapabilities(seekable=False, duration=None))
        engine.load(HttpSource(url="http://example.invalid/radio", seekable=False))
        before = engine.position

        engine.seek(timedelta(seconds=30))

        assert engine.position == before

    def test_seek_moves_position_when_seekable(
        self, engine: AudioEngine, audio_fixtures: AudioFixtures
    ) -> None:
        recorder = Recorder(engine)
        engine.load(LocalFileSource(path=audio_fixtures.valid))
        recorder.wait_until(lambda: engine.state == TransportState.PAUSED)
        capabilities = engine.capabilities
        assert capabilities is not None and capabilities.seekable

        engine.seek(timedelta(seconds=1))

        if isinstance(engine, FakeAudioEngine):
            assert engine.position == timedelta(seconds=1)
        else:
            recorder.wait_until(
                lambda: (engine.position or timedelta(0)) >= timedelta(milliseconds=900), timeout=3
            )


# ---------------------------------------------------------------------------
# Volume
# ---------------------------------------------------------------------------


class TestVolume:
    def test_gain_curve_is_cubic(self) -> None:
        assert gain_for_volume(0) == 0.0
        assert gain_for_volume(100) == pytest.approx(1.0)
        assert gain_for_volume(50) == pytest.approx(0.125)

    def test_set_volume_is_applied_inside_the_pipeline(self, engine: AudioEngine) -> None:
        """ADR 0003 / ADR 0006 § 6: volume changes the pipeline's own gain,
        never the system mixer — reading the value back is what actually
        verifies that rule rather than trusting the implementation."""
        engine.set_volume(50)
        if isinstance(engine, FakeAudioEngine):
            assert engine.last_gain == pytest.approx(0.125)
        else:
            assert engine._pipeline.get_property("volume") == pytest.approx(0.125)


# ---------------------------------------------------------------------------
# CONTENT-class failures discoverable from a local file alone — shared
# fixtures drive both engines, since both genuinely inspect the same file.
# ---------------------------------------------------------------------------


class TestContentFailures:
    def test_missing_source(self, engine: AudioEngine, audio_fixtures: AudioFixtures) -> None:
        recorder = Recorder(engine)
        engine.load(LocalFileSource(path=audio_fixtures.missing))
        recorder.wait_until(lambda: engine.state == TransportState.FAILED)
        assert recorder.failures[-1].code == FailureCode.SOURCE_MISSING
        assert recorder.failures[-1].failure_class == FailureClass.CONTENT

    def test_unreadable_source(self, engine: AudioEngine, audio_fixtures: AudioFixtures) -> None:
        if os.geteuid() == 0:
            pytest.skip("running as root ignores file permission bits")
        recorder = Recorder(engine)
        engine.load(LocalFileSource(path=audio_fixtures.unreadable))
        recorder.wait_until(lambda: engine.state == TransportState.FAILED)
        assert recorder.failures[-1].code == FailureCode.SOURCE_UNREADABLE
        assert recorder.failures[-1].failure_class == FailureClass.CONTENT

    def test_codec_unsupported(self, engine: AudioEngine, audio_fixtures: AudioFixtures) -> None:
        recorder = Recorder(engine)
        engine.load(LocalFileSource(path=audio_fixtures.codec_unsupported))
        recorder.wait_until(lambda: engine.state == TransportState.FAILED)
        assert recorder.failures[-1].code == FailureCode.CODEC_UNSUPPORTED
        assert recorder.failures[-1].failure_class == FailureClass.CONTENT

    def test_decode_failed(self, engine: AudioEngine, audio_fixtures: AudioFixtures) -> None:
        """The fake cannot tell a corrupted-but-typefindable file from a good
        one without a real decoder, so it is told what the real engine
        discovers on its own from the same bytes."""
        recorder = Recorder(engine)
        if isinstance(engine, FakeAudioEngine):
            engine.force_next_load_failure(
                FailureCode.DECODE_FAILED, "corrupt frame data (scripted)"
            )
        engine.load(LocalFileSource(path=audio_fixtures.corrupt))
        recorder.wait_until(lambda: engine.state == TransportState.FAILED)
        assert recorder.failures[-1].code == FailureCode.DECODE_FAILED
        assert recorder.failures[-1].failure_class == FailureClass.CONTENT

    def test_no_gstreamer_text_reaches_the_code(
        self, engine: AudioEngine, audio_fixtures: AudioFixtures
    ) -> None:
        """FAILURE_STATES.md: no GStreamer message text may cross the port
        boundary except inside `AudioFailure.detail`."""
        recorder = Recorder(engine)
        engine.load(LocalFileSource(path=audio_fixtures.missing))
        recorder.wait_until(lambda: engine.state == TransportState.FAILED)
        assert recorder.failures[-1].code.value == "source_missing"


# ---------------------------------------------------------------------------
# Stream (network) failures — a real local HTTP server, no external network.
# ---------------------------------------------------------------------------


def _closed_port() -> int:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()  # closed again: nothing is listening, connections are refused
    return port


def _drop_after_partial_handler(payload: bytes) -> type[http.server.BaseHTTPRequestHandler]:
    """An HTTP handler that trickles `payload` out in small, briefly-paced
    chunks and drops the connection at the halfway point.

    The pacing (not a test-body sleep — this runs in the server's own
    background thread) is what makes the failure land reliably *after*
    playback has started rather than during the initial connection: sending
    the whole partial payload in one burst let `playbin3` finish prerolling
    and fail before `play()` ever landed, which produced `STREAM_UNREACHABLE`
    instead of the mid-playback `STREAM_INTERRUPTED` this is meant to
    provoke (verified empirically before settling on this shape)."""

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "audio/flac")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            chunk_size = 8192
            sent = 0
            try:
                while sent < len(payload) // 2:
                    piece = payload[sent : sent + chunk_size]
                    self.wfile.write(piece)
                    self.wfile.flush()
                    sent += len(piece)
                    time.sleep(0.1)
            except OSError:
                pass  # the client may already have given up; that is fine
            finally:
                self.connection.close()

        def log_message(self, format: str, *args: object) -> None:
            pass  # keep test output quiet

    return Handler


@pytest.mark.parametrize("impl", ["fake", "real"])
class TestStreamFailures:
    def test_stream_unreachable(self, impl: str) -> None:
        port = _closed_port()
        engine = _make_engine(impl)
        recorder = Recorder(engine)
        if isinstance(engine, FakeAudioEngine):
            engine.force_next_load_failure(FailureCode.STREAM_UNREACHABLE, "connection refused")
        engine.load(HttpSource(url=f"http://127.0.0.1:{port}/missing.flac", seekable=False))
        try:
            recorder.wait_until(lambda: engine.state == TransportState.FAILED)
            assert recorder.failures[-1].code == FailureCode.STREAM_UNREACHABLE
            assert recorder.failures[-1].failure_class == FailureClass.CONTENT
        finally:
            _close_engine(engine)

    def test_stream_interrupted(self, impl: str, audio_fixtures: AudioFixtures) -> None:
        handler_cls = _drop_after_partial_handler(audio_fixtures.stream_payload)
        httpd = socketserver.TCPServer(("127.0.0.1", 0), handler_cls)
        port = httpd.server_address[1]
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()

        engine = _make_engine(impl)
        recorder = Recorder(engine)
        try:
            engine.load(HttpSource(url=f"http://127.0.0.1:{port}/stream.flac", seekable=False))
            recorder.wait_until(lambda: engine.state == TransportState.PAUSED)
            engine.play()
            recorder.wait_until(lambda: engine.state == TransportState.PLAYING)

            if isinstance(engine, FakeAudioEngine):
                engine.simulate_mid_playback_failure(
                    FailureCode.STREAM_INTERRUPTED, "connection dropped"
                )
            recorder.wait_until(lambda: engine.state == TransportState.FAILED, timeout=10)

            assert recorder.failures[-1].code == FailureCode.STREAM_INTERRUPTED
            assert recorder.failures[-1].failure_class == FailureClass.TRANSIENT
        finally:
            _close_engine(engine)
            httpd.shutdown()
            httpd.server_close()


# ---------------------------------------------------------------------------
# Device failures
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("impl", ["fake", "real"])
def test_audio_device_missing(impl: str, audio_fixtures: AudioFixtures) -> None:
    """Provoked with a deliberately nonexistent ALSA device name for the real
    engine — no Reference hardware needed, and no hardware absence to fake
    either: `hw:99,0` fails to open the same way an actually-absent sound
    card would."""
    if impl == "real":
        sink = Gst.ElementFactory.make("alsasink", None)
        sink.set_property("device", "hw:99,0")
        engine: AudioEngine = GStreamerAudioEngine(audio_sink=sink)
    else:
        engine = FakeAudioEngine()
        engine.force_next_load_failure(FailureCode.AUDIO_DEVICE_MISSING, "no such device")

    recorder = Recorder(engine)
    try:
        engine.load(LocalFileSource(path=audio_fixtures.valid))
        recorder.wait_until(lambda: engine.state == TransportState.FAILED)
        assert recorder.failures[-1].code == FailureCode.AUDIO_DEVICE_MISSING
        assert recorder.failures[-1].failure_class == FailureClass.DEVICE
    finally:
        _close_engine(engine)


def test_audio_device_lost_fake(audio_fixtures: AudioFixtures) -> None:
    engine = FakeAudioEngine()
    recorder = Recorder(engine)
    engine.load(LocalFileSource(path=audio_fixtures.valid))
    recorder.wait_until(lambda: engine.state == TransportState.PAUSED)
    engine.play()
    recorder.wait_until(lambda: engine.state == TransportState.PLAYING)

    engine.simulate_mid_playback_failure(FailureCode.AUDIO_DEVICE_LOST, "device unplugged")

    recorder.wait_until(lambda: engine.state == TransportState.FAILED)
    assert recorder.failures[-1].code == FailureCode.AUDIO_DEVICE_LOST
    assert recorder.failures[-1].failure_class == FailureClass.DEVICE


@pytest.mark.hardware
def test_audio_device_lost_real_requires_physical_unplug() -> None:
    """Unlike `AUDIO_DEVICE_MISSING`, there is no software-only way to make a
    *healthy* ALSA device disappear mid-stream — `fakesink` never opens a
    device to lose, and a bogus device fails at open time (`MISSING`), not
    mid-playback. Run manually on Reference hardware: start playback through
    a real sink, physically unplug the audio output, and confirm the engine
    reports `AUDIO_DEVICE_LOST`."""
    pytest.skip("manual: unplug the audio device during real playback")


# ---------------------------------------------------------------------------
# Gapless transitions — ADR 0009 § 4a, the part most likely to be faked badly.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("impl", ["fake", "real"])
def test_prepared_next_transitions_gaplessly(impl: str, audio_fixtures: AudioFixtures) -> None:
    """What this proves for the real engine: across the whole run — load,
    play, both ~2s clips back to back — the recorded state sequence never
    contains anything but the ordinary `LOADING -> PAUSED -> PLAYING` lead-in
    followed eventually by `STOPPED`, and `on_finished` never fires for the
    first clip. That is exactly what "the pipeline never returns to a
    non-playing state across the transition" and "no EOS reaches on_finished
    when a next source was prepared" mean operationally, and it is real,
    clock-paced GStreamer state (`fakesink(sync=True)`), not a mocked one.

    What it does not prove: that the audio samples themselves are
    click/gap-free at the sample level — this suite has no audio device to
    listen with, only the transport's own account of its state. It also does
    not prove the timing margin holds for a much shorter final buffer than
    ~2s; `about-to-finish`'s lead time is queue-level, not host our test
    controls precisely.
    """
    engine = _make_engine(impl, audio_sink=_fakesink() if impl == "real" else None)
    recorder = Recorder(engine)
    try:
        engine.load(LocalFileSource(path=audio_fixtures.gapless_first))
        # Queue the known successor before waiting for preroll. `playbin3` may
        # emit `about-to-finish` during preroll when the source fits into its
        # internal queue, so waiting for PAUSED can already be too late.
        engine.prepare_next(LocalFileSource(path=audio_fixtures.gapless_second))
        recorder.wait_until(lambda: engine.state == TransportState.PAUSED)

        engine.play()
        recorder.wait_until(lambda: engine.state == TransportState.PLAYING)

        if isinstance(engine, FakeAudioEngine):
            engine.simulate_finished()
            assert recorder.finished_count == 0
            assert engine.state is TransportState.PLAYING
            engine.simulate_finished()
        else:
            recorder.wait_until(lambda: engine.state == TransportState.STOPPED, timeout=10)

        assert recorder.finished_count == 1
        assert recorder.source_changes == [LocalFileSource(path=audio_fixtures.gapless_second)]

        non_playing = [state for state in recorder.states if state is not TransportState.PLAYING]
        # STOPPED appears only once both clips are exhausted — nothing at the
        # prepared boundary interrupts PLAYING.
        assert non_playing == [
            TransportState.LOADING,
            TransportState.PAUSED,
            TransportState.STOPPED,
        ]
    finally:
        _close_engine(engine)


def test_prepare_next_none_clears_the_armed_source(audio_fixtures: AudioFixtures) -> None:
    """`prepare_next(None)` must cancel a previously armed chapter — verified
    against the fake, whose `simulate_finished()` makes the outcome directly
    observable; the real engine's `about-to-finish` handler applies the same
    `None`-clears rule (`gstreamer_engine.py::_on_about_to_finish`)."""
    engine = FakeAudioEngine()
    recorder = Recorder(engine)
    engine.load(LocalFileSource(path=audio_fixtures.gapless_first))
    recorder.wait_until(lambda: engine.state == TransportState.PAUSED)
    engine.prepare_next(LocalFileSource(path=audio_fixtures.gapless_second))
    engine.prepare_next(None)
    engine.play()
    recorder.wait_until(lambda: engine.state == TransportState.PLAYING)

    engine.simulate_finished()

    assert recorder.finished_count == 1
    assert engine.state == TransportState.STOPPED
