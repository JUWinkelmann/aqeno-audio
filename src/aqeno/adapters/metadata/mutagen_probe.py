"""`MediaProbe` backed by `mutagen` — ADR 0014 § 1, CONTENT_INGESTION.md § 12.

The only module in the whole codebase that imports `mutagen`. Everything it
returns crosses the `MediaProbe` port as a `ProbedFile` — no `mutagen` type
ever leaves this file.

Chapter extraction covers what mutagen exposes cleanly: ID3 `CHAP` frames (MP3)
and the FLAC `CUESHEET` block. MP4/`.m4b` chapter atoms are not extracted —
mutagen has no built-in reader for the `chpl`/Nero chapter atoms, and writing
one is a container-parsing project of its own. `.m4b` files still classify as
`AUDIOBOOK` (CONTENT_INGESTION.md § 5 rule 3) and still play; they fall back to
one chapter per file like any other multi-file work, or one whole-file chapter
when there is only one.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import timedelta
from pathlib import Path

import mutagen
import mutagen.flac
import mutagen.id3

from aqeno.domain.content import Fingerprint, ReplayGain
from aqeno.ports.media_probe import ProbedChapter, ProbedFile

logger = logging.getLogger(__name__)

_FINGERPRINT_WINDOW = 64 * 1024

_PICTURE_MIME_EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


def _fingerprint(path: Path, size_bytes: int) -> Fingerprint:
    """`size_bytes` plus a blake2b-128 digest of the 64 KiB window at the
    midpoint — audio payload, not the header a tag editor rewrites
    (CONTENT_INGESTION.md § 4)."""
    window = min(_FINGERPRINT_WINDOW, size_bytes)
    offset = 0 if size_bytes <= _FINGERPRINT_WINDOW else size_bytes // 2
    with path.open("rb") as handle:
        handle.seek(offset)
        data = handle.read(window)
    digest = hashlib.blake2b(data, digest_size=16).digest()
    return Fingerprint(size_bytes=size_bytes, digest=digest)


def _first_easy(easy: object, key: str) -> str | None:
    if easy is None:
        return None
    try:
        values = easy[key]  # type: ignore[index]
    except Exception:
        return None
    if not values:
        return None
    return str(values[0])


def _track_number(easy: object) -> int | None:
    raw = _first_easy(easy, "tracknumber")
    if raw is None:
        return None
    head = raw.split("/")[0].strip()
    try:
        return int(head)
    except ValueError:
        return None


def _replaygain(easy: object) -> ReplayGain:
    def _float(key: str) -> float | None:
        raw = _first_easy(easy, key)
        if raw is None:
            return None
        try:
            return float(raw.replace("dB", "").strip())
        except ValueError:
            return None

    return ReplayGain(
        track_gain_db=_float("replaygain_track_gain"),
        track_peak=_float("replaygain_track_peak"),
        album_gain_db=_float("replaygain_album_gain"),
        album_peak=_float("replaygain_album_peak"),
    )


def _id3_chapters(tags: object) -> tuple[ProbedChapter, ...]:
    getall = getattr(tags, "getall", None)
    if getall is None:
        return ()
    frames = getall("CHAP")
    if not frames:
        return ()
    ordered = sorted(frames, key=lambda f: f.start_time)
    chapters = []
    for frame in ordered:
        title = None
        for sub in getattr(frame, "sub_frames", {}).values():
            if getattr(sub, "FrameID", None) == "TIT2":
                title = str(sub)
                break
        start = timedelta(milliseconds=frame.start_time)
        end_time = frame.end_time
        duration = (
            timedelta(milliseconds=end_time - frame.start_time)
            if end_time is not None and end_time != 0xFFFFFFFF
            else None
        )
        chapters.append(ProbedChapter(title=title, start=start, duration=duration))
    return tuple(chapters)


def _flac_cue_chapters(audio: object, total: timedelta | None) -> tuple[ProbedChapter, ...]:
    cuesheet = getattr(audio, "cuesheet", None)
    if cuesheet is None:
        return ()
    tracks = [t for t in getattr(cuesheet, "tracks", ()) if t.track_number != 170]  # 170 = lead-out
    if not tracks:
        return ()
    sample_rate = getattr(getattr(audio, "info", None), "sample_rate", None) or 44100
    starts = [timedelta(seconds=t.start_offset / sample_rate) for t in tracks]
    chapters = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else total
        duration = (end - start) if end is not None else None
        chapters.append(ProbedChapter(title=None, start=start, duration=duration))
    return tuple(chapters)


def _artwork(audio: object) -> tuple[bytes | None, str | None]:
    # FLAC/Ogg: `.pictures`. ID3: `APIC` frames. MP4: `covr` atom.
    pictures = getattr(audio, "pictures", None)
    if pictures:
        pic = pictures[0]
        return pic.data, pic.mime

    tags = getattr(audio, "tags", None)
    if tags is not None:
        getall = getattr(tags, "getall", None)
        if getall is not None:
            apics = getall("APIC")
            if apics:
                return apics[0].data, apics[0].mime
        try:
            covr = tags.get("covr")
        except Exception:
            covr = None
        if covr:
            image_format = getattr(covr[0], "imageformat", None)
            mime = "image/png" if image_format == 14 else "image/jpeg"  # mutagen.mp4.AtomDataType
            return bytes(covr[0]), mime

    return None, None


class MutagenProbe:
    """Implements `aqeno.ports.media_probe.MediaProbe`."""

    def probe(self, path: Path) -> ProbedFile | None:
        try:
            size_bytes = path.stat().st_size
            mtime = path.stat().st_mtime
        except OSError as exc:
            logger.warning("source unreadable: %s (%s)", path, exc)
            return None

        try:
            audio = mutagen.File(path)
        except Exception as exc:  # mutagen raises many distinct error types
            logger.warning("codec unsupported or file corrupt: %s (%s)", path, exc)
            return None
        if audio is None or audio.info is None:
            logger.warning("codec unsupported: %s", path)
            return None

        duration = timedelta(seconds=audio.info.length) if audio.info.length is not None else None
        if duration is None:
            return None

        try:
            easy = mutagen.File(path, easy=True)
        except Exception:
            easy = None

        try:
            fingerprint = _fingerprint(path, size_bytes)
        except OSError as exc:
            logger.warning("source unreadable while fingerprinting: %s (%s)", path, exc)
            return None

        chapters = _id3_chapters(getattr(audio, "tags", None))
        if not chapters and isinstance(audio, mutagen.flac.FLAC):
            chapters = _flac_cue_chapters(audio, duration)

        artwork, artwork_mime = _artwork(audio)

        return ProbedFile(
            path=path,
            size_bytes=size_bytes,
            mtime=mtime,
            fingerprint=fingerprint,
            duration=duration,
            title=_first_easy(easy, "title"),
            album=_first_easy(easy, "album"),
            genre=_first_easy(easy, "genre"),
            track_number=_track_number(easy),
            language=_first_easy(easy, "language"),
            chapters=chapters,
            artwork=artwork,
            artwork_mime=artwork_mime,
            replaygain=_replaygain(easy),
        )
