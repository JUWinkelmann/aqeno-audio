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

from datetime import timedelta
from enum import StrEnum, auto
from typing import Protocol

from aqeno.config.defaults import Settings
from aqeno.domain.content import ContentId, ContentItem
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


class TagMapping(Protocol):
    """Structural shape of a stored NFC tag mapping — see `adapters` for the
    concrete dataclass. Declared here only so callers can type against it without
    importing an adapter."""

    uid: str
    content_id: ContentId


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
    def upsert_content(self, item: ContentItem) -> None:
        """Insert or replace a content item, its sources and its chapters."""
        ...

    def get_content(self, content_id: ContentId) -> ContentItem | None: ...

    def list_content(self) -> tuple[ContentItem, ...]: ...

    def remove_content(self, content_id: ContentId) -> None:
        """Removes the content item and cascades to its tag mappings and resume
        positions. Never triggered by removing a tag mapping — only the reverse."""
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
