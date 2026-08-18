"""Consistent SQLite online snapshots shared by migration and backup."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from aqeno.adapters.persistence.migrations import get_schema_version


class SnapshotError(RuntimeError):
    pass


def sqlite_online_snapshot(source_path: Path, destination: Path) -> int:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".partial")
    if partial.exists():
        partial.unlink()
    source = sqlite3.connect(f"file:{source_path}?mode=ro", uri=True, timeout=5)
    target = sqlite3.connect(partial)
    try:
        source.backup(target)
        target.commit()
        integrity = target.execute("PRAGMA integrity_check").fetchone()
        if integrity is None or integrity[0] != "ok":
            raise SnapshotError(f"SQLite snapshot failed integrity check: {integrity}")
        version = get_schema_version(target)
    except BaseException:
        target.close()
        source.close()
        if partial.exists():
            partial.unlink()
        raise
    target.close()
    source.close()
    os.replace(partial, destination)
    return version
