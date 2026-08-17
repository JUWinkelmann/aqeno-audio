"""In-memory persistence fakes — used by tests and the fake-hardware run target.

Implement the same `aqeno.ports.persistence` Protocols as the real SQLite/TOML
adapters, with the same externally-visible behaviour: a tag mapping cannot
reference nonexistent content, removing content cascades to its mappings and
resume positions (never the reverse), and a resume write is skipped when the
position has not advanced. `tests/contracts/test_persistence.py` runs the same
suite against both, so this cannot drift from the adapter without a test noticing
(ADR 0008 § 3).
"""

from __future__ import annotations

import logging
from dataclasses import replace
from datetime import timedelta

from aqeno.config.defaults import Settings, default_settings
from aqeno.domain.content import ContentId, ContentItem
from aqeno.domain.profile import Profile
from aqeno.ports.persistence import DatabaseHealth, TagMapping, UnknownContentError

logger = logging.getLogger(__name__)


class FakeLibrary:
    """In-memory stand-in for `SqliteLibrary`. No file, no process boundary."""

    def __init__(self, *, health: DatabaseHealth = DatabaseHealth.OK) -> None:
        self._health = health
        self._content: dict[ContentId, ContentItem] = {}
        self._tags: dict[str, ContentId] = {}
        self._profiles: dict[str, Profile] = {}
        self._resume: dict[tuple[ContentId, str], timedelta] = {}
        self.closed = False

    # -- lifecycle -----------------------------------------------------------

    def health(self) -> DatabaseHealth:
        return self._health

    def close(self) -> None:
        self.closed = True

    def _degraded(self) -> bool:
        if self._health is DatabaseHealth.DEGRADED_READ_ONLY:
            logger.warning("persistence is degraded (read-only filesystem); write discarded")
            return True
        return False

    # -- content ---------------------------------------------------------------

    def save_content(self, item: ContentItem) -> None:
        if self._degraded():
            return
        self._content[item.id] = item

    def get_content(self, content_id: ContentId) -> ContentItem | None:
        return self._content.get(content_id)

    def list_content(self) -> tuple[ContentItem, ...]:
        return tuple(sorted(self._content.values(), key=lambda item: item.title))

    def remove_content(self, content_id: ContentId) -> None:
        if self._degraded():
            return
        self._content.pop(content_id, None)
        for uid in [uid for uid, cid in self._tags.items() if cid == content_id]:
            del self._tags[uid]
        for key in [key for key in self._resume if key[0] == content_id]:
            del self._resume[key]

    # -- tag mappings --------------------------------------------------------

    def map_tag(self, uid: str, content_id: ContentId) -> None:
        if self._degraded():
            return
        if content_id not in self._content:
            raise UnknownContentError(f"no such content: {content_id.value}")
        self._tags[uid] = content_id

    def resolve_tag(self, uid: str) -> ContentId | None:
        return self._tags.get(uid)

    def unmap_tag(self, uid: str) -> None:
        if self._degraded():
            return
        self._tags.pop(uid, None)

    def list_tags(self) -> tuple[TagMapping, ...]:
        return tuple(TagMapping(uid=uid, content_id=cid) for uid, cid in sorted(self._tags.items()))

    # -- profiles ----------------------------------------------------------

    def save_profile(self, profile: Profile) -> None:
        if self._degraded():
            return
        self._profiles[profile.name] = profile

    def get_profile(self, name: str) -> Profile | None:
        return self._profiles.get(name)

    def list_profiles(self) -> tuple[Profile, ...]:
        return tuple(sorted(self._profiles.values(), key=lambda profile: profile.name))

    # -- resume ------------------------------------------------------------

    def get_resume(self, content_id: ContentId, profile_name: str) -> timedelta | None:
        return self._resume.get((content_id, profile_name))

    def set_resume(self, content_id: ContentId, profile_name: str, position: timedelta) -> None:
        if self._degraded():
            return
        key = (content_id, profile_name)
        existing = self._resume.get(key)
        if existing is not None and existing >= position:
            return
        self._resume[key] = position


class FakeSettingsStore:
    """In-memory stand-in for `TomlSettingsStore`. No file, always valid input."""

    def __init__(self, *, initial: Settings | None = None) -> None:
        self._settings = initial if initial is not None else default_settings()

    def load(self) -> Settings:
        return self._settings

    def save(self, settings: Settings) -> None:
        self._settings = replace(settings)
