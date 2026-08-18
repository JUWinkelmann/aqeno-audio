"""Forward-only schema migrations — ADR 0007 § 5.

Each migration is a numbered function that mutates a `sqlite3.Connection`. All
pending migrations run in a single transaction, and the database file is copied
to a `.bak-<version>` sibling before any migration touches it — on a device that
can lose power at any moment, a mid-migration crash without a backup is how a
library gets lost.

A database whose recorded version is newer than `CURRENT_SCHEMA_VERSION` refuses
to open (`SchemaTooNewError`): downgrading silently is worse than failing.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from pathlib import Path

from aqeno.ports.persistence import SchemaTooNewError

Migration = Callable[[sqlite3.Connection], None]


_MIGRATION_0001_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE content (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        kind TEXT NOT NULL,
        duration_seconds REAL,
        artwork TEXT,
        language TEXT,
        kind_overridden INTEGER NOT NULL DEFAULT 0,
        available INTEGER NOT NULL DEFAULT 1
    )
    """,
    """
    CREATE TABLE content_source (
        content_id TEXT NOT NULL REFERENCES content(id) ON DELETE CASCADE,
        ordinal INTEGER NOT NULL,
        source_type TEXT NOT NULL CHECK (source_type IN ('local_file', 'http')),
        path TEXT,
        url TEXT,
        seekable INTEGER,
        PRIMARY KEY (content_id, ordinal)
    )
    """,
    """
    CREATE TABLE chapter (
        content_id TEXT NOT NULL REFERENCES content(id) ON DELETE CASCADE,
        idx INTEGER NOT NULL,
        title TEXT,
        start_seconds REAL NOT NULL,
        duration_seconds REAL,
        source_path TEXT,
        PRIMARY KEY (content_id, idx)
    )
    """,
    """
    CREATE TABLE profile (
        name TEXT PRIMARY KEY,
        level TEXT NOT NULL,
        role TEXT NOT NULL,
        ambient_enabled INTEGER NOT NULL DEFAULT 0,
        inactivity_timeout_seconds REAL NOT NULL,
        night_timeout_seconds REAL NOT NULL,
        allows_dim INTEGER NOT NULL,
        dim_hold_seconds REAL,
        interactive_brightness INTEGER NOT NULL,
        dim_brightness INTEGER NOT NULL,
        ambient_brightness INTEGER NOT NULL,
        night_brightness INTEGER NOT NULL,
        led_brightness INTEGER NOT NULL,
        volume_maximum INTEGER NOT NULL,
        volume_night_maximum INTEGER NOT NULL,
        volume_headphone_maximum INTEGER NOT NULL
    )
    """,
    # Deleting a tag mapping never touches content: the foreign key points the
    # other way. Deleting content cascades to its own mappings, never the
    # reverse (DOMAIN_MODEL.md invariants).
    """
    CREATE TABLE tag_mapping (
        uid TEXT PRIMARY KEY,
        content_id TEXT NOT NULL REFERENCES content(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE resume_position (
        content_id TEXT NOT NULL REFERENCES content(id) ON DELETE CASCADE,
        profile_name TEXT NOT NULL,
        position_seconds REAL NOT NULL,
        updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
        PRIMARY KEY (content_id, profile_name)
    )
    """,
)


def _migration_0001_initial(conn: sqlite3.Connection) -> None:
    for statement in _MIGRATION_0001_STATEMENTS:
        conn.execute(statement)


# ADR 0014 / CONTENT_INGESTION.md § 11 — the first migration against a schema that
# may already hold data, which is why `_backup()` in `apply_migrations()` matters
# here more than it did for migration 1.
_MIGRATION_0002_STATEMENTS: tuple[str, ...] = (
    # `available` already exists from migration 1 (it was anticipated ahead of
    # scanning). `last_seen` and `kind_inference_rule` are new.
    "ALTER TABLE content ADD COLUMN last_seen REAL",
    "ALTER TABLE content ADD COLUMN kind_inference_rule TEXT",
    """
    CREATE TABLE member_file (
        content_id TEXT NOT NULL REFERENCES content(id) ON DELETE CASCADE,
        ordinal INTEGER NOT NULL,
        path TEXT NOT NULL,
        size_bytes INTEGER NOT NULL,
        fingerprint BLOB NOT NULL,
        mtime REAL NOT NULL,
        track_gain_db REAL,
        track_peak REAL,
        album_gain_db REAL,
        album_peak REAL,
        PRIMARY KEY (content_id, ordinal)
    )
    """,
    # The lookup this exists for: "does a stored member file already have this
    # fingerprint" runs once per file per scan (CONTENT_INGESTION.md § 11).
    "CREATE INDEX member_file_fingerprint ON member_file (size_bytes, fingerprint)",
)


def _migration_0002_ingestion(conn: sqlite3.Connection) -> None:
    for statement in _MIGRATION_0002_STATEMENTS:
        conn.execute(statement)


_MIGRATION_0003_STATEMENTS: tuple[str, ...] = (
    "CREATE INDEX content_title_order ON content (lower(title), id)",
    "CREATE INDEX content_kind_available ON content (kind, available)",
    "CREATE INDEX resume_recent ON resume_position (profile_name, updated_at DESC)",
    "CREATE INDEX member_file_path ON member_file (path)",
)


def _migration_0003_management_index(conn: sqlite3.Connection) -> None:
    for statement in _MIGRATION_0003_STATEMENTS:
        conn.execute(statement)


_MIGRATION_0004_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE collection (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE collection_member (
        collection_id TEXT NOT NULL REFERENCES collection(id) ON DELETE CASCADE,
        content_id TEXT NOT NULL REFERENCES content(id) ON DELETE CASCADE,
        PRIMARY KEY (collection_id, content_id)
    )
    """,
    """
    CREATE TABLE content_audience (
        content_id TEXT PRIMARY KEY REFERENCES content(id) ON DELETE CASCADE,
        mode TEXT NOT NULL CHECK (mode IN ('shared', 'selected_profiles'))
    )
    """,
    """
    CREATE TABLE content_audience_profile (
        content_id TEXT NOT NULL REFERENCES content(id) ON DELETE CASCADE,
        profile_name TEXT NOT NULL REFERENCES profile(name) ON DELETE CASCADE,
        PRIMARY KEY (content_id, profile_name)
    )
    """,
    """
    CREATE TABLE content_access_override (
        content_id TEXT NOT NULL REFERENCES content(id) ON DELETE CASCADE,
        profile_name TEXT NOT NULL REFERENCES profile(name) ON DELETE CASCADE,
        decision TEXT NOT NULL CHECK (decision IN ('allow', 'deny')),
        PRIMARY KEY (content_id, profile_name)
    )
    """,
    """
    CREATE TABLE collection_audience (
        collection_id TEXT PRIMARY KEY REFERENCES collection(id) ON DELETE CASCADE,
        mode TEXT NOT NULL CHECK (mode IN ('shared', 'selected_profiles'))
    )
    """,
    """
    CREATE TABLE collection_audience_profile (
        collection_id TEXT NOT NULL REFERENCES collection(id) ON DELETE CASCADE,
        profile_name TEXT NOT NULL REFERENCES profile(name) ON DELETE CASCADE,
        PRIMARY KEY (collection_id, profile_name)
    )
    """,
    """
    CREATE TABLE favorite (
        profile_name TEXT NOT NULL REFERENCES profile(name) ON DELETE CASCADE,
        content_id TEXT NOT NULL REFERENCES content(id) ON DELETE CASCADE,
        PRIMARY KEY (profile_name, content_id)
    )
    """,
    "CREATE INDEX collection_member_content ON collection_member (content_id, collection_id)",
    "CREATE INDEX favorite_profile ON favorite (profile_name, content_id)",
    "CREATE INDEX content_override_profile ON content_access_override (profile_name, content_id)",
    "CREATE INDEX content_audience_profile_lookup "
    "ON content_audience_profile (profile_name, content_id)",
    "CREATE INDEX collection_audience_profile_lookup "
    "ON collection_audience_profile (profile_name, collection_id)",
)


def _migration_0004_profile_content_access(conn: sqlite3.Connection) -> None:
    for statement in _MIGRATION_0004_STATEMENTS:
        conn.execute(statement)


MIGRATIONS: tuple[tuple[int, Migration], ...] = (
    (1, _migration_0001_initial),
    (2, _migration_0002_ingestion),
    (3, _migration_0003_management_index),
    (4, _migration_0004_profile_content_access),
)

CURRENT_SCHEMA_VERSION = MIGRATIONS[-1][0]


def get_schema_version(conn: sqlite3.Connection) -> int:
    exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    ).fetchone()
    if not exists:
        return 0
    row = conn.execute("SELECT version FROM schema_version").fetchone()
    return int(row[0]) if row else 0


def _backup(db_path: Path, version: int) -> None:
    if not db_path.exists() or db_path.stat().st_size == 0:
        return  # nothing to lose yet
    from aqeno.appliance.sqlite_snapshot import sqlite_online_snapshot

    backup_path = db_path.with_name(f"{db_path.name}.bak-{version}")
    if backup_path.exists():
        backup_path.unlink()
    sqlite_online_snapshot(db_path, backup_path)


def apply_migrations(conn: sqlite3.Connection, *, db_path: Path) -> None:
    """Bring the database to `CURRENT_SCHEMA_VERSION`, or raise.

    Raises `SchemaTooNewError` without changing anything if the database's
    recorded version is newer than this build understands.
    """
    version = get_schema_version(conn)
    if version > CURRENT_SCHEMA_VERSION:
        raise SchemaTooNewError(found=version, supported=CURRENT_SCHEMA_VERSION)

    pending = [(v, m) for v, m in MIGRATIONS if v > version]
    if not pending:
        return

    _backup(db_path, version)

    # Explicit transaction, not `with conn:` — DDL statements do not reliably
    # trigger Python's implicit-transaction heuristic, and "applied in one
    # transaction" (ADR 0007 § 5) must hold for CREATE TABLE too, not just DML.
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
        if conn.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0] == 0:
            conn.execute("INSERT INTO schema_version (version) VALUES (0)")
        for target_version, migration in pending:
            migration(conn)
            conn.execute("UPDATE schema_version SET version = ?", (target_version,))
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")
