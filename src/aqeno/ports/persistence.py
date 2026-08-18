"""Persistence port — ADR 0007.

Storage-agnostic. Standard library and `aqeno.domain` only: no `sqlite3`, no
`tomllib`, no filesystem path handling. Those belong to `adapters/persistence/`.
The Protocols here are implemented once for real (SQLite + TOML,
`adapters/persistence/`) and once as an in-memory fake
(`adapters/fakes/persistence.py`); `tests/contracts/test_persistence.py` runs the
same suite against both so the fake cannot silently drift from the adapter.

Two stores, split by who needs to read them (ADR 0007 § "Decision"):

- `Library` — domain data: content, sources, chapters, profiles, tag mappings and
  resume positions. Backed by SQLite in the real adapter.
- `SettingsStore` — the Manager tier of `CONFIGURATION_DEFAULTS.md` § 7: timeouts,
  brightness, volume ceilings, sleep timer, NFC debounce, language. Hand-editable,
  untrusted input. Backed by a TOML file in the real adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum, auto
from typing import Protocol

from aqeno.config.defaults import Settings
from aqeno.domain.access import (
    AccessDecision,
    Audience,
    Collection,
    CollectionId,
    EffectiveAccess,
)
from aqeno.domain.content import ContentId, ContentItem, ContentKind, Fingerprint, MemberFile
from aqeno.domain.profile import Profile


class DatabaseHealth(StrEnum):
    """Reported by `Library.health()`. ADR 0007 § "Degraded operation"."""

    OK = auto()
    DEGRADED_READ_ONLY = auto()
    """Filesystem is read-only or full: local playback works, nothing persists."""


class PersistenceError(Exception):
    """Base class for persistence failures that must not crash the process.

    Raised by adapter factory functions (e.g. `open_library`), never by the
    Protocol methods themselves once a store is open — a store that is open is
    expected to serve reads even in `DEGRADED_READ_ONLY` health.
    """


class DatabaseCorruptError(PersistenceError):
    """The database file exists but is not a valid, intact SQLite database.

    ADR 0007 § "Degraded operation": recovery is an explicit Manager action, never
    an automatic wipe. The caller must not delete or recreate the file on this
    error; it must surface it and stop.
    """


class UnknownContentError(PersistenceError):
    """Raised by `Library.map_tag` when `content_id` has no content row.

    The concrete expression of the schema-level rule that a tag mapping cannot
    reference content that does not exist (ADR 0007 § 2, `DOMAIN_MODEL.md`).
    """


class SchemaTooNewError(PersistenceError):
    """The database's `schema_version` is newer than the code understands.

    ADR 0007 § 5: downgrading silently is worse than failing, so this refuses to
    open rather than guess.
    """

    def __init__(self, *, found: int, supported: int) -> None:
        self.found = found
        self.supported = supported
        super().__init__(
            f"database schema version {found} is newer than the {supported} this "
            f"build understands; refusing to open"
        )


@dataclass(frozen=True, slots=True)
class TagMapping:
    uid: str
    content_id: ContentId


@dataclass(frozen=True, slots=True)
class ContentQuery:
    """Bounded local-index query for management and future richer Device UIs.

    The cursor tuple is the previous row's case-folded title and stable ContentId.
    It is deliberately persistence-neutral; HTTP encoding belongs to the adapter.
    """

    limit: int
    search: str | None = None
    kind: ContentKind | None = None
    available: bool | None = None
    after: tuple[str, ContentId] | None = None
    profile_name: str | None = None


@dataclass(frozen=True, slots=True)
class ContentPage:
    items: tuple[ContentItem, ...]
    total: int


class Library(Protocol):
    """Domain-data persistence. One connection/session per open `Library`.

    Implementations enforce, in the schema: deleting a tag mapping never deletes
    content (`DOMAIN_MODEL.md` invariants; ADR 0007 § 2).
    """

    def health(self) -> DatabaseHealth:
        """Current degraded/healthy status, established when the store was opened."""
        ...

    def close(self) -> None: ...

    # -- content -----------------------------------------------------------
    def save_content(
        self, item: ContentItem, *, member_files: tuple[MemberFile, ...] | None = None
    ) -> None:
        """Insert or replace a content item, its sources and its chapters.

        `member_files` is the scan-oriented path (CONTENT_INGESTION.md § 11):
        when given (including empty), it replaces the stored member-file
        records used by `find_by_fingerprint()`. Callers outside a scan simply
        omit it, leaving any previously stored member-file records untouched.
        """
        ...

    def get_content(self, content_id: ContentId) -> ContentItem | None: ...

    def list_content(self) -> tuple[ContentItem, ...]: ...

    def query_content(self, query: ContentQuery) -> ContentPage:
        """Server-side filtering and stable keyset pagination over the local index."""
        ...

    def remove_content(self, content_id: ContentId) -> None:
        """Removes the content item and cascades to its tag mappings and resume
        positions. Never triggered by removing a tag mapping — only the reverse."""
        ...

    def find_by_fingerprint(self, fingerprint: Fingerprint) -> ContentId | None:
        """The `ContentId` of the known work with a member file matching this
        fingerprint, or `None`. Ingestion identity resolution (CONTENT_INGESTION.md
        § 4) — a rescan recognises a file it has already seen at a new path.
        """
        ...

    def get_member_files(self, content_id: ContentId) -> tuple[MemberFile, ...]:
        """The stored member-file records for a work, as of the last scan.

        Identity resolution needs the *total* count to test "more than half of
        that work's stored member files matched" (CONTENT_INGESTION.md § 4).
        """
        ...

    def find_member_by_path(self, path: str) -> tuple[ContentId, MemberFile] | None:
        """Scan bookkeeping lookup; paths are locations, never public identity."""
        ...

    def mark_available(self, content_ids: tuple[ContentId, ...], *, last_seen: float) -> None: ...

    def mark_unavailable(self, content_ids: tuple[ContentId, ...]) -> None:
        """Sets `available = False` on every listed work, leaving everything else
        untouched — resume position, tag mappings and metadata all survive
        (CONTENT_INGESTION.md § 8). A work is never deleted by a scan.
        """
        ...

    # -- tag mappings --------------------------------------------------------
    def map_tag(self, uid: str, content_id: ContentId) -> None:
        """Raises if `content_id` does not exist — the schema's foreign key."""
        ...

    def resolve_tag(self, uid: str) -> ContentId | None: ...

    def unmap_tag(self, uid: str) -> None:
        """Removes the mapping only. Must never remove the referenced content."""
        ...

    def list_tags(self) -> tuple[TagMapping, ...]: ...

    # -- profiles --------------------------------------------------------------
    def save_profile(self, profile: Profile) -> None: ...

    def get_profile(self, name: str) -> Profile | None: ...

    def list_profiles(self) -> tuple[Profile, ...]: ...

    def remove_profile(self, name: str) -> None: ...

    # -- personal listening state --------------------------------------------
    def set_favorite(self, profile_name: str, content_id: ContentId, favorite: bool) -> None: ...

    def is_favorite(self, profile_name: str, content_id: ContentId) -> bool: ...

    def list_favorites(self, profile_name: str, query: ContentQuery) -> ContentPage: ...

    # -- content access -------------------------------------------------------
    def set_content_audience(
        self, content_ids: tuple[ContentId, ...], audience: Audience
    ) -> None: ...

    def set_content_overrides(
        self,
        content_ids: tuple[ContentId, ...],
        profile_names: tuple[str, ...],
        decision: AccessDecision | None,
    ) -> None: ...

    def get_content_audience(self, content_id: ContentId) -> Audience | None: ...

    def effective_access(self, content_id: ContentId, profile_name: str) -> EffectiveAccess: ...

    def can_profile_access(self, content_id: ContentId, profile_name: str) -> bool: ...

    # -- collections ----------------------------------------------------------
    def save_collection(self, collection: Collection) -> None: ...

    def get_collection(self, collection_id: CollectionId) -> Collection | None: ...

    def list_collections(self) -> tuple[Collection, ...]: ...

    def remove_collection(self, collection_id: CollectionId) -> None: ...

    def set_collection_audience(self, collection_id: CollectionId, audience: Audience) -> None: ...

    def get_collection_audience(self, collection_id: CollectionId) -> Audience | None: ...

    # -- resume ------------------------------------------------------------
    def get_resume(self, content_id: ContentId, profile_name: str) -> timedelta | None: ...

    def set_resume(self, content_id: ContentId, profile_name: str, position: timedelta) -> None:
        """Persists a resume position.

        `CONFIGURATION_DEFAULTS.md` § 4: a write is skipped when the position has
        not advanced past the stored one — paused playback writes nothing.
        """
        ...


class SettingsStore(Protocol):
    """The TOML settings store. Untrusted input: `load()` never raises on a
    malformed file — it clamps, defaults, logs, and leaves the file alone."""

    def load(self) -> Settings: ...

    def save(self, settings: Settings) -> None:
        """Atomic write: temp file in the same directory, fsync it, `os.replace`,
        fsync the directory (ADR 0007 § "Decision" / § 1)."""
        ...
