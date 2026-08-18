"""MediaProbe port — ADR 0014 § 1, CONTENT_INGESTION.md § 12.

Reads container/tag data from one file. No adapter type crosses this boundary —
`ProbedFile` is built entirely from the standard library plus `aqeno.domain`, so
`application/ingestion.py` can depend on it without depending on `mutagen`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Protocol

from aqeno.domain.content import Fingerprint, ReplayGain


@dataclass(frozen=True, slots=True)
class ProbedChapter:
    """One chapter embedded in a container — MP4 chapter atoms, ID3 `CHAP`
    frames, or a FLAC `CUESHEET` block. `start` is the offset within this file.
    """

    title: str | None
    start: timedelta
    duration: timedelta | None


@dataclass(frozen=True, slots=True)
class ProbedFile:
    """Everything ingestion needs from one file, read from headers only —
    probing never decodes audio (ADR 0014 § 1).
    """

    path: Path
    size_bytes: int
    mtime: float
    fingerprint: Fingerprint
    duration: timedelta | None
    title: str | None = None
    album: str | None = None
    genre: str | None = None
    track_number: int | None = None
    language: str | None = None
    chapters: tuple[ProbedChapter, ...] = ()
    """Non-empty only for a single-file work with embedded/CUESHEET chapters."""
    artwork: bytes | None = None
    artwork_mime: str | None = None
    replaygain: ReplayGain = field(default_factory=ReplayGain)


class MediaProbe(Protocol):
    def probe(self, path: Path) -> ProbedFile | None:
        """Reads headers and the fingerprint window.

        Returns `None` when the file cannot be read or its container/codec is
        not understood — `FAILURE_STATES.md` codes `source_unreadable` and
        `codec_unsupported`. Never raises for those cases; ingestion excludes
        the file from its work and continues (CONTENT_INGESTION.md § 10).
        """
        ...
