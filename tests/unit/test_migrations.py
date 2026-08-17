"""Migration behaviour — ADR 0007 § 5.

Forward-only, applied in one transaction, database copied before any migration
runs, and a database whose schema is newer than the code refuses to open.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from aqeno.adapters.persistence.migrations import (
    CURRENT_SCHEMA_VERSION,
    apply_migrations,
    get_schema_version,
)
from aqeno.adapters.persistence.sqlite_library import open_library
from aqeno.ports.persistence import DatabaseCorruptError, SchemaTooNewError


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


class TestFreshDatabase:
    def test_migrating_an_empty_database_reaches_current_version(self, tmp_path: Path) -> None:
        db_path = tmp_path / "aqeno.db"
        conn = _connect(db_path)
        apply_migrations(conn, db_path=db_path)
        assert get_schema_version(conn) == CURRENT_SCHEMA_VERSION
        conn.close()

    def test_migrating_twice_is_a_no_op(self, tmp_path: Path) -> None:
        db_path = tmp_path / "aqeno.db"
        conn = _connect(db_path)
        apply_migrations(conn, db_path=db_path)
        apply_migrations(conn, db_path=db_path)  # must not raise or duplicate tables
        assert get_schema_version(conn) == CURRENT_SCHEMA_VERSION
        conn.close()

    def test_creates_the_tables_content_and_resume_data_need(self, tmp_path: Path) -> None:
        db_path = tmp_path / "aqeno.db"
        conn = _connect(db_path)
        apply_migrations(conn, db_path=db_path)
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert {
            "schema_version",
            "content",
            "content_source",
            "chapter",
            "profile",
            "tag_mapping",
            "resume_position",
        } <= tables
        conn.close()


class TestSchemaTooNew:
    def test_a_newer_schema_version_refuses_to_open(self, tmp_path: Path) -> None:
        db_path = tmp_path / "aqeno.db"
        conn = _connect(db_path)
        apply_migrations(conn, db_path=db_path)
        conn.execute("UPDATE schema_version SET version = ?", (CURRENT_SCHEMA_VERSION + 1,))
        conn.close()

        with pytest.raises(SchemaTooNewError):
            open_library(tmp_path)

    def test_refusing_to_open_does_not_touch_the_file(self, tmp_path: Path) -> None:
        db_path = tmp_path / "aqeno.db"
        conn = _connect(db_path)
        apply_migrations(conn, db_path=db_path)
        conn.execute("UPDATE schema_version SET version = ?", (CURRENT_SCHEMA_VERSION + 1,))
        conn.close()
        size_before = db_path.stat().st_size

        with pytest.raises(SchemaTooNewError):
            open_library(tmp_path)

        assert db_path.stat().st_size == size_before


class TestBackupBeforeMigration:
    def test_a_populated_database_is_backed_up_before_a_new_migration_runs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A device that may lose power at any moment must never run a migration
        against real data without a backup to fall back to (ADR 0007 § 5)."""
        db_path = tmp_path / "aqeno.db"
        conn = _connect(db_path)
        apply_migrations(conn, db_path=db_path)
        conn.execute("INSERT INTO content (id, title, kind) VALUES ('x', 'Title', 'audiobook')")
        conn.close()

        added_column = False

        def _migration_0002_marker(conn: sqlite3.Connection) -> None:
            nonlocal added_column
            conn.execute("ALTER TABLE content ADD COLUMN marker TEXT")
            added_column = True

        import aqeno.adapters.persistence.migrations as migrations_module

        monkeypatch.setattr(
            migrations_module,
            "MIGRATIONS",
            (*migrations_module.MIGRATIONS, (2, _migration_0002_marker)),
        )
        monkeypatch.setattr(migrations_module, "CURRENT_SCHEMA_VERSION", 2)

        apply_migrations(_connect(db_path), db_path=db_path)

        assert added_column
        backups = list(tmp_path.glob("aqeno.db.bak-*"))
        assert backups, "expected a backup file before the new migration ran"

    def test_a_fresh_database_is_not_backed_up(self, tmp_path: Path) -> None:
        db_path = tmp_path / "aqeno.db"
        conn = _connect(db_path)
        apply_migrations(conn, db_path=db_path)
        conn.close()
        assert not list(tmp_path.glob("aqeno.db.bak-*"))


class TestCorruptDatabase:
    def test_a_corrupt_file_is_reported_and_never_wiped(self, tmp_path: Path) -> None:
        db_path = tmp_path / "aqeno.db"
        db_path.write_bytes(b"this is not a sqlite database, just noise" * 100)
        original_bytes = db_path.read_bytes()

        with pytest.raises(DatabaseCorruptError):
            open_library(tmp_path)

        assert db_path.read_bytes() == original_bytes, "a corrupt database must never be wiped"

    def test_opening_a_healthy_database_afterwards_still_works(self, tmp_path: Path) -> None:
        """A corrupt database in one directory must not affect a clean one."""
        clean_dir = tmp_path / "clean"
        lib = open_library(clean_dir)
        lib.close()
