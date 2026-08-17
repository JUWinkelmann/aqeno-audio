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

import shutil
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


MIGRATIONS: tuple[tuple[int, Migration], ...] = ((1, _migration_0001_initial),)

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
    backup_path = db_path.with_name(f"{db_path.name}.bak-{version}")
    shutil.copy2(db_path, backup_path)
    for suffix in ("-wal", "-shm"):
        side_file = db_path.with_name(db_path.name + suffix)
        if side_file.exists():
            shutil.copy2(side_file, backup_path.with_name(backup_path.name + suffix))


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
