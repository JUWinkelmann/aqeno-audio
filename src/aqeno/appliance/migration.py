"""Non-destructive, resumable migration from the reference-service prototype."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aqeno.appliance.sqlite_snapshot import sqlite_online_snapshot
from aqeno.appliance.storage import capacity_status
from aqeno.config.paths import AqenoPaths


class MigrationConflictError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class MigrationResult:
    copied: tuple[str, ...]
    already_present: tuple[str, ...]
    source_found: bool


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


def _write_json_atomic(path: Path, value: Mapping[str, Any]) -> None:
    """Persist migration progress without ever exposing a partial journal."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.partial")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        raise


def _stage_file(source: Path, staged: Path, *, database: bool) -> None:
    staged.parent.mkdir(parents=True, exist_ok=True)
    if database:
        sqlite_online_snapshot(source, staged)
        return
    temporary = staged.with_name(f".{staged.name}.partial")
    if temporary.exists():
        temporary.unlink()
    try:
        shutil.copy2(source, temporary)
        if _digest(source) != _digest(temporary):
            raise RuntimeError(f"failed to validate staged migration file: {source}")
        os.replace(temporary, staged)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        raise


def _inventory(config_root: Path, legacy_root: Path) -> list[tuple[Path, Path, bool]]:
    entries: list[tuple[Path, Path, bool]] = []
    settings = config_root / "settings.toml"
    database = legacy_root / "aqeno.db"
    if settings.is_file():
        entries.append((settings, Path("state/config/settings.toml"), False))
    if database.is_file():
        entries.append((database, Path("state/aqeno.db"), True))
    for name, target in (
        ("management.key", Path("state/secrets/management.key")),
        ("device-id", Path("state/identity/device-id")),
    ):
        device_state = legacy_root / "state" / name
        if device_state.is_file():
            entries.append((device_state, target, False))
    for source_name, target_name in (("artwork", "state/artwork/original"), ("media", "media")):
        source_root = legacy_root / source_name
        if source_root.is_dir():
            entries.extend(
                (path, Path(target_name) / path.relative_to(source_root), False)
                for path in sorted(source_root.rglob("*"))
                if path.is_file()
            )
    return entries


def migrate_prototype_data(
    layout: AqenoPaths,
    *,
    legacy_config: Path = Path("/etc/aqeno"),
    legacy_data: Path = Path("/var/lib/aqeno"),
) -> MigrationResult:
    completion = layout.state / "prototype-migration.json"
    if completion.is_file():
        try:
            completed = json.loads(completion.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise MigrationConflictError("prototype migration marker is unreadable") from exc
        if completed.get("state") != "complete":
            raise MigrationConflictError("prototype migration marker is incomplete")
        completed_paths = tuple(str(value) for value in completed.get("copied", []))
        return MigrationResult((), completed_paths, True)

    entries = _inventory(legacy_config, legacy_data)
    if not entries:
        return MigrationResult((), (), False)
    estimated_payload = sum(source.stat().st_size for source, _relative, _database in entries)
    if not capacity_status(layout.data_root).permits(estimated_payload):
        raise MigrationConflictError("insufficient reserved AQENO-DATA capacity for migration")

    staging = layout.temporary / "migration" / "prototype-v1"
    journal = staging / "migration.json"
    committed: set[str] = set()
    planned: dict[str, str] = {}
    if journal.is_file():
        try:
            progress = json.loads(journal.read_text(encoding="utf-8"))
            committed = {str(value) for value in progress.get("committed", [])}
            raw_planned = progress.get("planned", {})
            if not isinstance(raw_planned, dict):
                raise ValueError("planned inventory is not an object")
            planned = {str(key): str(value) for key, value in raw_planned.items()}
        except (OSError, json.JSONDecodeError) as exc:
            raise MigrationConflictError("interrupted migration journal is unreadable") from exc
        except (TypeError, ValueError) as exc:
            raise MigrationConflictError("interrupted migration journal is invalid") from exc
        if committed and not planned:
            raise MigrationConflictError("interrupted migration journal lacks an inventory")

    conflicts: list[str] = []
    already: list[str] = []
    for source, relative, is_database in entries:
        relative_name = relative.as_posix()
        target = layout.data_root / relative
        if not target.exists():
            continue
        expected = planned.get(relative_name)
        if expected is not None and target.is_file() and _digest(target) == expected:
            # This also closes the power-loss window between target activation
            # and the following journal fsync.
            committed.add(relative_name)
            already.append(relative_name)
        elif is_database:
            # A target database means two independently writable states may exist.
            conflicts.append(relative_name)
        elif target.is_file() and _digest(source) == _digest(target):
            already.append(relative_name)
        else:
            conflicts.append(relative_name)
    if conflicts:
        raise MigrationConflictError("target contains differing state: " + ", ".join(conflicts))

    migration_id = str(uuid.uuid4())
    staging.mkdir(parents=True, exist_ok=True)
    _write_json_atomic(
        journal,
        {"state": "preparing", "committed": sorted(committed), "planned": planned},
    )
    copied_paths: list[str] = []
    try:
        for source, relative, is_database in entries:
            relative_name = relative.as_posix()
            target = layout.data_root / relative
            if relative_name in already or relative_name in committed:
                continue
            staged = staging / relative
            expected = planned.get(relative_name)
            if not staged.is_file() or expected is None or _digest(staged) != expected:
                _stage_file(source, staged, database=is_database)
            planned[relative_name] = _digest(staged)
        _write_json_atomic(
            journal,
            {"state": "validated", "committed": sorted(committed), "planned": planned},
        )
        for _source, relative, _is_database in entries:
            relative_name = relative.as_posix()
            if relative_name in already or relative_name in committed:
                continue
            staged = staging / relative
            target = layout.data_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                raise MigrationConflictError(f"target appeared during migration: {relative}")
            os.replace(staged, target)
            copied_paths.append(relative_name)
            committed.add(relative_name)
            _write_json_atomic(
                journal,
                {"state": "committing", "committed": sorted(committed), "planned": planned},
            )
        record = completion
        record.parent.mkdir(parents=True, exist_ok=True)
        migrated = sorted(planned)
        _write_json_atomic(
            record,
            {
                "state": "complete",
                "migration_id": migration_id,
                "copied": migrated,
                "already_present": sorted(set(already) - set(migrated)),
            },
        )
    except BaseException:
        raise
    else:
        shutil.rmtree(staging, ignore_errors=True)
    return MigrationResult(tuple(copied_paths), tuple(already), True)
