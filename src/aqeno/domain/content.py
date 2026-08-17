"""Content identity, kinds and their playback behaviour.

Implements `docs/decisions/0009-content-kinds.md` and the `Content != Source`
separation from `docs/implementation/DOMAIN_MODEL.md`.

The key rule: no code branches on `ContentKind` outside `policy_for()`. Behaviour is
a policy lookup, the same capability-driven pattern used for profiles.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import timedelta
from enum import StrEnum, auto
from pathlib import Path


class ContentKind(StrEnum):
    MUSIC_TRACK = auto()
    MUSIC_ALBUM = auto()
    AUDIO_DRAMA = auto()
    AUDIOBOOK = auto()
    PODCAST_EPISODE = auto()
    RADIO_STREAM = auto()
    PERSONAL_RECORDING = auto()


class TransportBehaviour(StrEnum):
    """What Next/Previous mean — the "contextual" in PRODUCT_FOUNDATION.md § 5."""

    TRACK = auto()
    """Next/previous track in the collection."""
    CHAPTER_ELSE_SKIP = auto()
    """Next/previous chapter; where there are none, skip by a time step."""
    IGNORED = auto()
    """Radio has nothing to skip to."""


@dataclass(frozen=True, slots=True)
class KindPolicy:
    transport: TransportBehaviour
    exact_resume: bool
    shuffle_permitted: bool
    advance_within_collection: bool
    skip_forward: timedelta | None = None
    skip_back: timedelta | None = None
    restart_threshold: timedelta | None = None
    """Previous restarts the current item if more than this far in (music convention)."""
    resume_minimum_duration: timedelta | None = None
    """Items shorter than this restart from the beginning rather than resuming."""


_SKIP_FORWARD = timedelta(seconds=60)
_SKIP_BACK = timedelta(seconds=30)
"""Asymmetric on purpose: recovering your place needs more context than you skipped."""

_LONG_FORM = KindPolicy(
    transport=TransportBehaviour.CHAPTER_ELSE_SKIP,
    exact_resume=True,
    shuffle_permitted=False,
    advance_within_collection=True,
    skip_forward=_SKIP_FORWARD,
    skip_back=_SKIP_BACK,
)

_MUSIC = KindPolicy(
    transport=TransportBehaviour.TRACK,
    exact_resume=False,
    shuffle_permitted=True,
    advance_within_collection=True,
    restart_threshold=timedelta(seconds=3),
    resume_minimum_duration=timedelta(minutes=10),
)

_POLICIES: dict[ContentKind, KindPolicy] = {
    ContentKind.MUSIC_TRACK: _MUSIC,
    ContentKind.MUSIC_ALBUM: _MUSIC,
    ContentKind.AUDIO_DRAMA: _LONG_FORM,
    ContentKind.AUDIOBOOK: _LONG_FORM,
    ContentKind.PODCAST_EPISODE: KindPolicy(
        transport=TransportBehaviour.CHAPTER_ELSE_SKIP,
        exact_resume=True,
        shuffle_permitted=False,
        advance_within_collection=False,
        skip_forward=_SKIP_FORWARD,
        skip_back=_SKIP_BACK,
    ),
    ContentKind.RADIO_STREAM: KindPolicy(
        transport=TransportBehaviour.IGNORED,
        exact_resume=False,
        shuffle_permitted=False,
        advance_within_collection=False,
    ),
    ContentKind.PERSONAL_RECORDING: KindPolicy(
        transport=TransportBehaviour.TRACK,
        exact_resume=True,
        shuffle_permitted=False,
        advance_within_collection=False,
    ),
}


def policy_for(kind: ContentKind) -> KindPolicy:
    return _POLICIES[kind]


@dataclass(frozen=True, slots=True)
class ContentId:
    """Stable AQENO identity, generated once and never derived from a file path.

    Moving a file breaks *resolution*, not identity: the item keeps its resume
    position and tag mappings (ADR 0007 § 3).
    """

    value: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass(frozen=True, slots=True)
class Chapter:
    index: int
    title: str | None
    start: timedelta
    duration: timedelta | None
    source: LocalFileSource | None = None
    """Set when the chapter is its own file, as in a folder of ripped CD tracks."""


@dataclass(frozen=True, slots=True)
class LocalFileSource:
    path: Path


@dataclass(frozen=True, slots=True)
class HttpSource:
    url: str
    seekable: bool = False


Source = LocalFileSource | HttpSource


@dataclass(frozen=True, slots=True)
class ContentItem:
    """A work, not a file. Forty MP3s of one audiobook are one item with forty
    chapters — Kids Early shows very few large tiles (ADR 0009 § 4).
    """

    id: ContentId
    title: str
    kind: ContentKind
    sources: tuple[Source, ...]
    chapters: tuple[Chapter, ...] = ()
    duration: timedelta | None = None
    artwork: Path | None = None
    language: str | None = None
    """Content language, independent of UI language (ADR 0005, ADR 0009)."""
    kind_overridden: bool = False
    """True when a Manager corrected an inferred kind. Tags lie constantly."""

    @property
    def policy(self) -> KindPolicy:
        return policy_for(self.kind)

    @property
    def has_chapters(self) -> bool:
        return len(self.chapters) > 1

    @property
    def is_stream(self) -> bool:
        return self.kind is ContentKind.RADIO_STREAM
