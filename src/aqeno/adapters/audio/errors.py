"""GStreamer bus-error to `FailureCode` mapping — ADR 0003, `FAILURE_STATES.md`.

This is the boundary where GStreamer's technical error surface stops. No
`GLib.Error`, no `Gst` type and no GStreamer message text crosses back out of
`map_bus_error`: the caller gets an `AudioFailure`, whose `code` is the stable
identifier the UI and logs depend on and whose `detail` is logs/Manager-only
technical text (`FAILURE_STATES.md` rule 5).

`gi` may be imported only under `adapters/` (`DEVELOPMENT.md` rule 1). This module
is where every `Gst.ResourceError` / `Gst.StreamError` / `Gst.CoreError` /
`Gst.LibraryError` comparison happens, once, so `gstreamer_engine.py` never touches
one directly.
"""

from __future__ import annotations

import logging
from enum import StrEnum, auto

import gi

gi.require_version("Gst", "1.0")
from gi.repository import GLib, Gst  # noqa: E402

from aqeno.ports.audio import AudioFailure, FailureCode

logger = logging.getLogger(__name__)


class SourceKind(StrEnum):
    """Which `Source` variant was loaded when the error arrived.

    GStreamer reports the same resource-error codes for "local file not found"
    and "network resource not reachable" — `Gst.ResourceError.NOT_FOUND` and
    `Gst.ResourceError.OPEN_READ` mean different things for a `LocalFileSource`
    than for an `HttpSource`. Only the caller knows which one is loaded, so it is
    passed in rather than guessed from the message text (which this module must
    not inspect for classification — only for `AudioFailure.detail`).
    """

    LOCAL_FILE = auto()
    HTTP = auto()


def map_bus_error(
    gerror: GLib.Error,
    debug: str | None,
    *,
    source_kind: SourceKind,
    was_playing: bool,
) -> AudioFailure:
    """Translate one GStreamer bus `ERROR` message into an `AudioFailure`.

    `was_playing` disambiguates errors that mean different things depending on
    whether playback had already started: a read failure while still loading is
    `SOURCE_UNREADABLE` / `STREAM_UNREACHABLE`, the same failure after playback
    had started is `STREAM_INTERRUPTED` / `AUDIO_DEVICE_LOST`.
    """
    code = _classify(gerror, source_kind=source_kind, was_playing=was_playing)
    detail = f"{gerror.message} (domain={gerror.domain} code={gerror.code})"
    if debug:
        detail += f" debug={debug}"
    return AudioFailure(code=code, detail=detail)


def _classify(gerror: GLib.Error, *, source_kind: SourceKind, was_playing: bool) -> FailureCode:
    matches = gerror.matches
    resource = Gst.resource_error_quark()
    stream = Gst.stream_error_quark()
    core = Gst.core_error_quark()

    # -- resource errors: opening or reading the source itself -----------------
    if matches(resource, Gst.ResourceError.NOT_FOUND):
        return (
            FailureCode.SOURCE_MISSING
            if source_kind is SourceKind.LOCAL_FILE
            else FailureCode.STREAM_UNREACHABLE
        )
    if matches(resource, Gst.ResourceError.OPEN_READ):
        return (
            FailureCode.SOURCE_UNREADABLE
            if source_kind is SourceKind.LOCAL_FILE
            else FailureCode.STREAM_UNREACHABLE
        )
    if matches(resource, Gst.ResourceError.NOT_AUTHORIZED):
        return (
            FailureCode.SOURCE_UNREADABLE
            if source_kind is SourceKind.LOCAL_FILE
            else FailureCode.STREAM_UNREACHABLE
        )
    if matches(resource, Gst.ResourceError.READ):
        if was_playing:
            # Read failed after playback had already started, local or
            # network: the source was working and stopped working.
            return FailureCode.STREAM_INTERRUPTED
        return (
            FailureCode.STREAM_UNREACHABLE
            if source_kind is SourceKind.HTTP
            else FailureCode.SOURCE_UNREADABLE
        )

    # -- resource errors: the audio sink / output device ------------------------
    if matches(resource, Gst.ResourceError.OPEN_WRITE) or matches(resource, Gst.ResourceError.WRITE):
        return FailureCode.AUDIO_DEVICE_LOST if was_playing else FailureCode.AUDIO_DEVICE_MISSING
    if matches(resource, Gst.ResourceError.SETTINGS) or matches(resource, Gst.ResourceError.BUSY):
        return FailureCode.AUDIO_DEVICE_MISSING
    if matches(resource, Gst.ResourceError.SYNC):
        return FailureCode.AUDIO_DEVICE_LOST

    # -- stream errors: container / codec vs. decode failure --------------------
    if (
        matches(stream, Gst.StreamError.CODEC_NOT_FOUND)
        or matches(stream, Gst.StreamError.TYPE_NOT_FOUND)
        or matches(stream, Gst.StreamError.WRONG_TYPE)
        or matches(stream, Gst.StreamError.DECRYPT)
        or matches(stream, Gst.StreamError.DECRYPT_NOKEY)
    ):
        return FailureCode.CODEC_UNSUPPORTED
    if (
        matches(stream, Gst.StreamError.DECODE)
        or matches(stream, Gst.StreamError.DEMUX)
        or matches(stream, Gst.StreamError.FORMAT)
    ):
        return FailureCode.DECODE_FAILED

    # -- core errors: mostly pipeline-internal, but two map cleanly -------------
    if matches(core, Gst.CoreError.MISSING_PLUGIN):
        return FailureCode.CODEC_UNSUPPORTED
    if matches(core, Gst.CoreError.NEGOTIATION):
        return FailureCode.CODEC_UNSUPPORTED

    # Everything else — notably Gst.StreamError.FAILED, which is what
    # `souphttpsrc` raises for a refused/unreachable TCP connection (it never
    # gets far enough to produce a GST_RESOURCE_ERROR), plus
    # Gst.CoreError.{TOO_LAZY,NOT_IMPLEMENTED,STATE_CHANGE,PAD,THREAD,EVENT,
    # SEEK,CAPS,TAG,CLOCK,DISABLED}, Gst.LibraryError.*, and
    # Gst.ResourceError.{CLOSE,NO_SPACE_LEFT,OPEN_READ_WRITE} — has no clean
    # home in FAILURE_STATES.md's eight audio codes. Rather than crash or drop
    # the message, it is logged in full and reported as the closest generic
    # case available: a network source that failed before or during playback
    # is a stream problem; anything else is a decode problem.
    if source_kind is SourceKind.HTTP:
        fallback = FailureCode.STREAM_INTERRUPTED if was_playing else FailureCode.STREAM_UNREACHABLE
    else:
        fallback = FailureCode.DECODE_FAILED
    logger.warning(
        "unmapped GStreamer error, reporting as %s: domain=%s code=%s message=%s",
        fallback,
        gerror.domain,
        gerror.code,
        gerror.message,
    )
    return fallback
