"""`map_bus_error` — the boundary where GStreamer's error surface stops.

`FAILURE_STATES.md`: "The audio adapter maps every GStreamer bus error onto one
of [the eight audio failure codes]." This test constructs a `GLib.Error` for
every domain/code pair `errors.py` recognises, plus a representative sample of
codes it does not, and checks the mapping and the no-GStreamer-text-in-`code`
rule (only `detail` may carry it).
"""

from __future__ import annotations

import gi
import pytest

gi.require_version("Gst", "1.0")
from gi.repository import GLib, Gst  # noqa: E402

from aqeno.adapters.audio.errors import SourceKind, map_bus_error
from aqeno.ports.audio import FailureClass, FailureCode

Gst.init(None)


def _error(quark: int, code: int, message: str = "technical message") -> GLib.Error:
    return GLib.Error.new_literal(quark, message, code)


RESOURCE = Gst.resource_error_quark()
STREAM = Gst.stream_error_quark()
CORE = Gst.core_error_quark()
LIBRARY = Gst.library_error_quark()

# (quark, code, source_kind, was_playing, expected)
MAPPED_CASES = [
    # -- resource: opening/reading the source itself -------------------------
    (RESOURCE, Gst.ResourceError.NOT_FOUND, SourceKind.LOCAL_FILE, False, FailureCode.SOURCE_MISSING),
    (RESOURCE, Gst.ResourceError.NOT_FOUND, SourceKind.HTTP, False, FailureCode.STREAM_UNREACHABLE),
    (RESOURCE, Gst.ResourceError.OPEN_READ, SourceKind.LOCAL_FILE, False, FailureCode.SOURCE_UNREADABLE),
    (RESOURCE, Gst.ResourceError.OPEN_READ, SourceKind.HTTP, False, FailureCode.STREAM_UNREACHABLE),
    (
        RESOURCE,
        Gst.ResourceError.NOT_AUTHORIZED,
        SourceKind.LOCAL_FILE,
        False,
        FailureCode.SOURCE_UNREADABLE,
    ),
    (
        RESOURCE,
        Gst.ResourceError.NOT_AUTHORIZED,
        SourceKind.HTTP,
        False,
        FailureCode.STREAM_UNREACHABLE,
    ),
    (RESOURCE, Gst.ResourceError.READ, SourceKind.LOCAL_FILE, False, FailureCode.SOURCE_UNREADABLE),
    (RESOURCE, Gst.ResourceError.READ, SourceKind.LOCAL_FILE, True, FailureCode.STREAM_INTERRUPTED),
    (RESOURCE, Gst.ResourceError.READ, SourceKind.HTTP, False, FailureCode.STREAM_UNREACHABLE),
    (RESOURCE, Gst.ResourceError.READ, SourceKind.HTTP, True, FailureCode.STREAM_INTERRUPTED),
    # -- resource: the audio sink / output device -----------------------------
    (
        RESOURCE,
        Gst.ResourceError.OPEN_WRITE,
        SourceKind.LOCAL_FILE,
        False,
        FailureCode.AUDIO_DEVICE_MISSING,
    ),
    (RESOURCE, Gst.ResourceError.OPEN_WRITE, SourceKind.LOCAL_FILE, True, FailureCode.AUDIO_DEVICE_LOST),
    (RESOURCE, Gst.ResourceError.WRITE, SourceKind.LOCAL_FILE, True, FailureCode.AUDIO_DEVICE_LOST),
    (
        RESOURCE,
        Gst.ResourceError.SETTINGS,
        SourceKind.LOCAL_FILE,
        False,
        FailureCode.AUDIO_DEVICE_MISSING,
    ),
    (RESOURCE, Gst.ResourceError.BUSY, SourceKind.LOCAL_FILE, False, FailureCode.AUDIO_DEVICE_MISSING),
    (RESOURCE, Gst.ResourceError.SYNC, SourceKind.LOCAL_FILE, True, FailureCode.AUDIO_DEVICE_LOST),
    # -- stream: container / codec vs. decode failure --------------------------
    (
        STREAM,
        Gst.StreamError.CODEC_NOT_FOUND,
        SourceKind.LOCAL_FILE,
        False,
        FailureCode.CODEC_UNSUPPORTED,
    ),
    (
        STREAM,
        Gst.StreamError.TYPE_NOT_FOUND,
        SourceKind.LOCAL_FILE,
        False,
        FailureCode.CODEC_UNSUPPORTED,
    ),
    (STREAM, Gst.StreamError.WRONG_TYPE, SourceKind.LOCAL_FILE, False, FailureCode.CODEC_UNSUPPORTED),
    (STREAM, Gst.StreamError.DECRYPT, SourceKind.LOCAL_FILE, False, FailureCode.CODEC_UNSUPPORTED),
    (
        STREAM,
        Gst.StreamError.DECRYPT_NOKEY,
        SourceKind.LOCAL_FILE,
        False,
        FailureCode.CODEC_UNSUPPORTED,
    ),
    (STREAM, Gst.StreamError.DECODE, SourceKind.LOCAL_FILE, True, FailureCode.DECODE_FAILED),
    (STREAM, Gst.StreamError.DEMUX, SourceKind.LOCAL_FILE, False, FailureCode.DECODE_FAILED),
    (STREAM, Gst.StreamError.FORMAT, SourceKind.LOCAL_FILE, False, FailureCode.DECODE_FAILED),
    # -- core: negotiation / missing plugin are effectively codec problems ----
    (CORE, Gst.CoreError.MISSING_PLUGIN, SourceKind.LOCAL_FILE, False, FailureCode.CODEC_UNSUPPORTED),
    (CORE, Gst.CoreError.NEGOTIATION, SourceKind.LOCAL_FILE, False, FailureCode.CODEC_UNSUPPORTED),
]


@pytest.mark.parametrize(
    "quark,code,source_kind,was_playing,expected",
    MAPPED_CASES,
    ids=[f"{c[0]}-{c[1]}-{c[2]}-playing={c[3]}" for c in MAPPED_CASES],
)
def test_explicit_mappings(
    quark: int,
    code: int,
    source_kind: SourceKind,
    was_playing: bool,
    expected: FailureCode,
) -> None:
    gerror = _error(quark, code)
    failure = map_bus_error(gerror, "some debug text", source_kind=source_kind, was_playing=was_playing)
    assert failure.code is expected


def test_every_failure_code_is_reachable() -> None:
    """FAILURE_STATES.md's eight audio codes must all have at least one mapped
    case above — a code nothing maps to would be dead, undetectable code."""
    reached = {case[4] for case in MAPPED_CASES}
    assert reached == set(FailureCode)


# ---------------------------------------------------------------------------
# Unmapped errors: FAILURE_STATES.md requires every bus error to land
# *somewhere*, never crash and never silently vanish.
# ---------------------------------------------------------------------------

UNMAPPED_CASES = [
    (CORE, Gst.CoreError.FAILED, SourceKind.LOCAL_FILE, False, FailureCode.DECODE_FAILED),
    (CORE, Gst.CoreError.STATE_CHANGE, SourceKind.LOCAL_FILE, False, FailureCode.DECODE_FAILED),
    (CORE, Gst.CoreError.SEEK, SourceKind.LOCAL_FILE, False, FailureCode.DECODE_FAILED),
    (LIBRARY, Gst.LibraryError.FAILED, SourceKind.LOCAL_FILE, False, FailureCode.DECODE_FAILED),
    (RESOURCE, Gst.ResourceError.NO_SPACE_LEFT, SourceKind.LOCAL_FILE, False, FailureCode.DECODE_FAILED),
    # For an HTTP source, the same "nothing else fits" situation is a stream
    # problem, not a decode problem — souphttpsrc raises exactly
    # Gst.StreamError.FAILED for a refused TCP connection (verified against
    # the real adapter: no GST_RESOURCE_ERROR is ever produced for that case).
    (STREAM, Gst.StreamError.FAILED, SourceKind.HTTP, False, FailureCode.STREAM_UNREACHABLE),
    (STREAM, Gst.StreamError.FAILED, SourceKind.HTTP, True, FailureCode.STREAM_INTERRUPTED),
    (STREAM, Gst.StreamError.FAILED, SourceKind.LOCAL_FILE, False, FailureCode.DECODE_FAILED),
]


@pytest.mark.parametrize(
    "quark,code,source_kind,was_playing,expected",
    UNMAPPED_CASES,
    ids=[f"{c[0]}-{c[1]}-{c[2]}-playing={c[3]}" for c in UNMAPPED_CASES],
)
def test_unmapped_errors_fall_back_without_crashing(
    quark: int,
    code: int,
    source_kind: SourceKind,
    was_playing: bool,
    expected: FailureCode,
    caplog: pytest.LogCaptureFixture,
) -> None:
    gerror = _error(quark, code)
    failure = map_bus_error(gerror, "debug text", source_kind=source_kind, was_playing=was_playing)
    assert failure.code is expected
    assert "unmapped GStreamer error" in caplog.text


def test_no_gstreamer_text_crosses_into_code() -> None:
    """`FailureCode` is a closed `StrEnum` — GStreamer's message text can only
    ever end up in `detail`, never smuggled into `code` (FAILURE_STATES.md,
    `ports/audio.py`)."""
    gerror = _error(RESOURCE, Gst.ResourceError.NOT_FOUND, message="/home/user/secret/path.mp3")
    failure = map_bus_error(
        gerror, "debug", source_kind=SourceKind.LOCAL_FILE, was_playing=False
    )
    assert isinstance(failure.code, FailureCode)
    assert failure.code.value == "source_missing"
    assert "/home/user/secret/path.mp3" not in failure.code.value


def test_detail_carries_the_technical_message_for_logs_and_manager_only() -> None:
    gerror = _error(RESOURCE, Gst.ResourceError.NOT_FOUND, message="No such file")
    failure = map_bus_error(
        gerror, "gstfilesrc.c(585): no such file", source_kind=SourceKind.LOCAL_FILE, was_playing=False
    )
    assert "No such file" in failure.detail
    assert "gstfilesrc.c" in failure.detail


def test_device_missing_is_a_device_failure() -> None:
    """A closed-loop check that the code this module produces for a missing
    audio device lines up with `FAILURE_STATES.md`'s severity class via
    `ports/audio.py::classify` — not duplicated logic, just a sanity check
    that the two modules agree."""
    from aqeno.ports.audio import classify

    gerror = _error(RESOURCE, Gst.ResourceError.SETTINGS)
    failure = map_bus_error(gerror, None, source_kind=SourceKind.LOCAL_FILE, was_playing=False)
    assert classify(failure.code) is FailureClass.DEVICE
