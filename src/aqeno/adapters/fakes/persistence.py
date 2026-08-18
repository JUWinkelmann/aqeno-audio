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
from aqeno.domain.access import (
    AccessDecision,
    AccessSource,
    Audience,
    AudienceMode,
    Collection,
    CollectionId,
    EffectiveAccess,
)
from aqeno.domain.content import ContentId, ContentItem, Fingerprint, MemberFile
from aqeno.domain.profile import Profile
from aqeno.ports.persistence import (
    ContentPage,
    ContentQuery,
    DatabaseHealth,
    TagMapping,
    UnknownContentError,
)

logger = logging.getLogger(__name__)


class FakeLibrary:
    """In-memory stand-in for `SqliteLibrary`. No file, no process boundary."""

    def __init__(self, *, health: DatabaseHealth = DatabaseHealth.OK) -> None:
        self._health = health
        self._content: dict[ContentId, ContentItem] = {}
        self._member_files: dict[ContentId, tuple[MemberFile, ...]] = {}
        self._tags: dict[str, ContentId] = {}
        self._profiles: dict[str, Profile] = {}
        self._resume: dict[tuple[ContentId, str], timedelta] = {}
        self._favorites: set[tuple[str, ContentId]] = set()
        self._content_audiences: dict[ContentId, Audience] = {}
        self._content_overrides: dict[tuple[ContentId, str], AccessDecision] = {}
        self._collections: dict[CollectionId, Collection] = {}
        self._collection_audiences: dict[CollectionId, Audience] = {}
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

    def save_content(
        self, item: ContentItem, *, member_files: tuple[MemberFile, ...] | None = None
    ) -> None:
        if self._degraded():
            return
        self._content[item.id] = item
        if member_files is not None:
            self._member_files[item.id] = member_files

    def get_content(self, content_id: ContentId) -> ContentItem | None:
        return self._content.get(content_id)

    def list_content(self) -> tuple[ContentItem, ...]:
        return tuple(sorted(self._content.values(), key=lambda item: item.title))

    def query_content(self, query: ContentQuery) -> ContentPage:
        items = list(self._content.values())
        if query.profile_name is not None:
            items = [item for item in items if self.can_profile_access(item.id, query.profile_name)]
        if query.search is not None:
            needle = query.search.casefold()
            items = [item for item in items if needle in item.title.casefold()]
        if query.kind is not None:
            items = [item for item in items if item.kind is query.kind]
        if query.available is not None:
            items = [item for item in items if item.available is query.available]
        items.sort(key=lambda item: (item.title.casefold(), str(item.id.value)))
        total = len(items)
        if query.after is not None:
            after_title, after_id = query.after
            items = [
                item
                for item in items
                if (item.title.casefold(), str(item.id.value)) > (after_title, str(after_id.value))
            ]
        return ContentPage(items=tuple(items[: query.limit]), total=total)

    def remove_content(self, content_id: ContentId) -> None:
        if self._degraded():
            return
        self._content.pop(content_id, None)
        self._member_files.pop(content_id, None)
        for uid in [uid for uid, cid in self._tags.items() if cid == content_id]:
            del self._tags[uid]
        for key in [key for key in self._resume if key[0] == content_id]:
            del self._resume[key]
        self._favorites = {entry for entry in self._favorites if entry[1] != content_id}
        self._content_audiences.pop(content_id, None)
        for key in [key for key in self._content_overrides if key[0] == content_id]:
            del self._content_overrides[key]
        for collection_id, collection in tuple(self._collections.items()):
            self._collections[collection_id] = replace(
                collection,
                content_ids=tuple(cid for cid in collection.content_ids if cid != content_id),
            )

    def find_by_fingerprint(self, fingerprint: Fingerprint) -> ContentId | None:
        for content_id, members in self._member_files.items():
            for member in members:
                if member.fingerprint == fingerprint:
                    return content_id
        return None

    def get_member_files(self, content_id: ContentId) -> tuple[MemberFile, ...]:
        return self._member_files.get(content_id, ())

    def find_member_by_path(self, path: str) -> tuple[ContentId, MemberFile] | None:
        for content_id, members in self._member_files.items():
            for member in members:
                if str(member.path) == path:
                    return content_id, member
        return None

    def mark_available(self, content_ids: tuple[ContentId, ...], *, last_seen: float) -> None:
        if self._degraded():
            return
        for content_id in content_ids:
            item = self._content.get(content_id)
            if item is not None:
                self._content[content_id] = replace(item, available=True, last_seen=last_seen)

    def mark_unavailable(self, content_ids: tuple[ContentId, ...]) -> None:
        if self._degraded():
            return
        for content_id in content_ids:
            item = self._content.get(content_id)
            if item is not None:
                self._content[content_id] = replace(item, available=False)

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

    def remove_profile(self, name: str) -> None:
        if self._degraded():
            return
        self._profiles.pop(name, None)
        self._favorites = {entry for entry in self._favorites if entry[0] != name}
        self._content_overrides = {
            key: value for key, value in self._content_overrides.items() if key[1] != name
        }
        for content_id, audience in tuple(self._content_audiences.items()):
            self._content_audiences[content_id] = replace(
                audience, profile_names=tuple(p for p in audience.profile_names if p != name)
            )
        for collection_id, audience in tuple(self._collection_audiences.items()):
            self._collection_audiences[collection_id] = replace(
                audience, profile_names=tuple(p for p in audience.profile_names if p != name)
            )

    def set_favorite(self, profile_name: str, content_id: ContentId, favorite: bool) -> None:
        entry = (profile_name, content_id)
        if favorite:
            self._favorites.add(entry)
        else:
            self._favorites.discard(entry)

    def is_favorite(self, profile_name: str, content_id: ContentId) -> bool:
        return (profile_name, content_id) in self._favorites

    def list_favorites(self, profile_name: str, query: ContentQuery) -> ContentPage:
        page = self.query_content(replace(query, profile_name=profile_name, limit=10**9))
        items = [item for item in page.items if (profile_name, item.id) in self._favorites]
        total = len(items)
        return ContentPage(items=tuple(items[: query.limit]), total=total)

    def set_content_audience(self, content_ids: tuple[ContentId, ...], audience: Audience) -> None:
        for content_id in content_ids:
            self._content_audiences[content_id] = audience

    def set_content_overrides(
        self,
        content_ids: tuple[ContentId, ...],
        profile_names: tuple[str, ...],
        decision: AccessDecision | None,
    ) -> None:
        for content_id in content_ids:
            for profile_name in profile_names:
                key = (content_id, profile_name)
                if decision is None:
                    self._content_overrides.pop(key, None)
                else:
                    self._content_overrides[key] = decision

    def get_content_audience(self, content_id: ContentId) -> Audience | None:
        return self._content_audiences.get(content_id)

    def effective_access(self, content_id: ContentId, profile_name: str) -> EffectiveAccess:
        override = self._content_overrides.get((content_id, profile_name))
        if override is not None:
            return EffectiveAccess(
                allowed=override is AccessDecision.ALLOW,
                source=AccessSource.MEDIA_OVERRIDE,
                explicit_decision=override,
            )
        inherited = [
            collection_id
            for collection_id, collection in self._collections.items()
            if content_id in collection.content_ids and collection_id in self._collection_audiences
        ]
        if inherited:
            allowed = any(
                _audience_allows(self._collection_audiences[collection_id], profile_name)
                for collection_id in inherited
            )
            return EffectiveAccess(
                allowed=allowed,
                source=AccessSource.COLLECTION,
                inherited_collection_ids=tuple(inherited),
            )
        audience = self._content_audiences.get(content_id)
        if audience is not None:
            return EffectiveAccess(
                allowed=_audience_allows(audience, profile_name),
                source=AccessSource.MEDIA_AUDIENCE,
            )
        return EffectiveAccess(allowed=True, source=AccessSource.SHARED_DEFAULT)

    def can_profile_access(self, content_id: ContentId, profile_name: str) -> bool:
        return self.effective_access(content_id, profile_name).allowed

    def save_collection(self, collection: Collection) -> None:
        self._collections[collection.id] = collection

    def get_collection(self, collection_id: CollectionId) -> Collection | None:
        return self._collections.get(collection_id)

    def list_collections(self) -> tuple[Collection, ...]:
        return tuple(sorted(self._collections.values(), key=lambda item: item.name.casefold()))

    def remove_collection(self, collection_id: CollectionId) -> None:
        self._collections.pop(collection_id, None)
        self._collection_audiences.pop(collection_id, None)

    def set_collection_audience(self, collection_id: CollectionId, audience: Audience) -> None:
        self._collection_audiences[collection_id] = audience

    def get_collection_audience(self, collection_id: CollectionId) -> Audience | None:
        return self._collection_audiences.get(collection_id)

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


def _audience_allows(audience: Audience, profile_name: str) -> bool:
    return audience.mode is AudienceMode.SHARED or profile_name in audience.profile_names
