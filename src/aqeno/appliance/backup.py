"""Portable, atomic AQENO state backup (ADR 0020)."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from aqeno.adapters.persistence.migrations import CURRENT_SCHEMA_VERSION, get_schema_version
from aqeno.appliance.sqlite_snapshot import sqlite_online_snapshot
from aqeno.appliance.storage import capacity_status
from aqeno.config.paths import AqenoPaths

BACKUP_FORMAT_VERSION = 1
REQUIRED_COMPONENTS = frozenset({"database", "settings"})


class BackupError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class BackupEntry:
    path: str
    size: int
    sha256: str


@dataclass(frozen=True, slots=True)
class BackupValidation:
    valid: bool
    compatible: bool
    message: str
    manifest: dict[str, Any] | None = None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _entry(archive_path: str, source: Path) -> BackupEntry:
    return BackupEntry(archive_path, source.stat().st_size, _sha256(source))


def create_state_backup(
    layout: AqenoPaths,
    destination: Path,
    *,
    aqeno_version: str,
    now: datetime | None = None,
) -> Path:
    if destination.suffix != ".aqbackup":
        raise BackupError("state backup destination must end in .aqbackup")
    if not layout.database.is_file():
        raise BackupError(f"database is missing: {layout.database}")
    settings = layout.config / "settings.toml"
    if not settings.is_file():
        raise BackupError(f"settings are missing: {settings}")
    original_artwork = (
        [path for path in layout.original_artwork.rglob("*") if path.is_file()]
        if layout.original_artwork.is_dir()
        else []
    )
    estimated_payload = (
        layout.database.stat().st_size
        + settings.stat().st_size
        + sum(path.stat().st_size for path in original_artwork)
    )
    if not capacity_status(layout.data_root).permits(estimated_payload, staging_copies=2):
        raise BackupError("insufficient reserved AQENO-DATA capacity for state backup")
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".partial")
    if destination.exists() or partial.exists():
        raise FileExistsError(destination if destination.exists() else partial)

    layout.backup_staging.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=layout.backup_staging, prefix="state-") as staging_name:
        staging = Path(staging_name)
        snapshot = staging / "aqeno.db"
        schema_version = sqlite_online_snapshot(layout.database, snapshot)
        sources: list[tuple[str, Path]] = [
            ("state/aqeno.db", snapshot),
            ("state/config/settings.toml", settings),
        ]
        if original_artwork:
            sources.extend(
                (
                    f"state/artwork/original/{path.relative_to(layout.original_artwork).as_posix()}",
                    path,
                )
                for path in sorted(original_artwork)
            )
        entries = [_entry(archive_path, source) for archive_path, source in sources]
        components = ["database", "settings"]
        if len(sources) > 2:
            components.append("original_artwork")
        manifest = {
            "backup_format_version": BACKUP_FORMAT_VERSION,
            "aqeno_version": aqeno_version,
            "created_at": (now or datetime.now(UTC)).isoformat().replace("+00:00", "Z"),
            "schema_version": schema_version,
            "kind": "state",
            "included_components": components,
            "media_included": False,
            "entries": [asdict(entry) for entry in entries],
        }
        try:
            with zipfile.ZipFile(partial, "x", allowZip64=True) as archive:
                for archive_path, source in sources:
                    archive.write(source, archive_path)
                archive.writestr(
                    "manifest.json",
                    json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n",
                )
            validation = validate_state_backup(partial, allow_partial=True)
            if not validation.valid or not validation.compatible:
                raise BackupError(validation.message)
            with partial.open("rb") as handle:
                os.fsync(handle.fileno())
            os.replace(partial, destination)
            directory = os.open(destination.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except BaseException:
            if partial.exists():
                partial.unlink()
            raise
    return destination


def _safe_archive_path(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts


def validate_state_backup(path: Path, *, allow_partial: bool = False) -> BackupValidation:
    if path.name.endswith(".aqbackup.partial") and not allow_partial:
        return BackupValidation(False, False, "incomplete AQENO backup")
    if path.suffix != ".aqbackup" and not (
        allow_partial and path.name.endswith(".aqbackup.partial")
    ):
        return BackupValidation(False, False, "not an AQENO backup")
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            if "manifest.json" not in names or any(not _safe_archive_path(name) for name in names):
                return BackupValidation(False, False, "manifest missing or archive path unsafe")
            manifest = json.loads(archive.read("manifest.json"))
            if manifest.get("backup_format_version") != BACKUP_FORMAT_VERSION:
                return BackupValidation(False, False, "unsupported backup format", manifest)
            if manifest.get("kind") != "state" or manifest.get("media_included") is not False:
                return BackupValidation(False, False, "not a state backup", manifest)
            components = set(manifest.get("included_components", []))
            if not components >= REQUIRED_COMPONENTS:
                return BackupValidation(False, False, "required components missing", manifest)
            if int(manifest.get("schema_version", -1)) > CURRENT_SCHEMA_VERSION:
                return BackupValidation(
                    True, False, "database schema is newer than this AQENO", manifest
                )
            entries = manifest.get("entries")
            if not isinstance(entries, list):
                return BackupValidation(False, False, "entry inventory missing", manifest)
            entry_names: set[str] = set()
            for entry in entries:
                name = entry["path"]
                entry_names.add(name)
                if name not in names or not _safe_archive_path(name):
                    return BackupValidation(
                        False, False, f"missing or unsafe entry: {name}", manifest
                    )
                payload = archive.read(name)
                if len(payload) != int(entry["size"]):
                    return BackupValidation(False, False, f"size mismatch: {name}", manifest)
                if hashlib.sha256(payload).hexdigest() != entry["sha256"]:
                    return BackupValidation(False, False, f"checksum mismatch: {name}", manifest)
            if not {"state/aqeno.db", "state/config/settings.toml"} <= entry_names:
                return BackupValidation(False, False, "required state entries missing", manifest)
            with tempfile.TemporaryDirectory(prefix="aqeno-backup-validation-") as directory:
                db_path = Path(directory) / "aqeno.db"
                db_path.write_bytes(archive.read("state/aqeno.db"))
                import sqlite3

                conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
                try:
                    integrity = conn.execute("PRAGMA integrity_check").fetchone()
                    schema = get_schema_version(conn)
                finally:
                    conn.close()
                if integrity is None or integrity[0] != "ok":
                    return BackupValidation(
                        False, False, "database integrity check failed", manifest
                    )
                if schema != int(manifest["schema_version"]):
                    return BackupValidation(
                        False, False, "database schema does not match manifest", manifest
                    )
            return BackupValidation(True, True, "valid", manifest)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        zipfile.BadZipFile,
        json.JSONDecodeError,
    ) as exc:
        return BackupValidation(False, False, f"invalid backup: {exc}")
