"""Profile-scoped favourites and shared-by-default content access."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import StrEnum, auto

from aqeno.domain.content import ContentId


class AudienceMode(StrEnum):
    SHARED = auto()
    SELECTED_PROFILES = auto()


class AccessDecision(StrEnum):
    ALLOW = auto()
    DENY = auto()


class AccessSource(StrEnum):
    MEDIA_OVERRIDE = auto()
    COLLECTION = auto()
    MEDIA_AUDIENCE = auto()
    SHARED_DEFAULT = auto()


@dataclass(frozen=True, slots=True)
class CollectionId:
    value: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass(frozen=True, slots=True)
class Collection:
    id: CollectionId
    name: str
    content_ids: tuple[ContentId, ...] = ()


@dataclass(frozen=True, slots=True)
class Audience:
    mode: AudienceMode
    profile_names: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EffectiveAccess:
    allowed: bool
    source: AccessSource
    explicit_decision: AccessDecision | None = None
    inherited_collection_ids: tuple[CollectionId, ...] = ()
