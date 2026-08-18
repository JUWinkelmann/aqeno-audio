from __future__ import annotations

import json
import sqlite3
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import pytest

from aqeno.adapters.local_assets import InsufficientCapacityError, LocalAssetStore
from aqeno.adapters.persistence.migrations import (
    CURRENT_SCHEMA_VERSION,
    apply_migrations,
    get_schema_version,
)
from aqeno.appliance import backup as backup_module
from aqeno.appliance import migration as migration_module
from aqeno.appliance.backup import BackupError, create_state_backup, validate_state_backup
from aqeno.appliance.migration import MigrationConflictError, migrate_prototype_data
from aqeno.appliance.sqlite_snapshot import sqlite_online_snapshot
from aqeno.appliance.storage import (
    GIB,
    CapacityLevel,
    CapacityStatus,
    VolumeProblem,
    VolumeValidationError,
    capacity_status,
    create_data_layout,
    create_volume_marker,
    validate_data_volume,
)
from aqeno.config.paths import AqenoPaths


@dataclass(frozen=True)
class Usage:
    total: int
    used: int
    free: int


def _layout(root: Path) -> AqenoPaths:
    state = root / "state"
    return AqenoPaths(
        appliance=True,
        application_root=Path("/opt/aqeno"),
        data_root=root,
        config=state / "config",
        database=state / "aqeno.db",
        state=state,
        media=root / "media",
        original_artwork=state / "artwork" / "original",
        derived_artwork=root / "cache" / "artwork",
        cache=root / "cache",
        temporary=root / "tmp",
        import_staging=root / "tmp" / "imports",
        backup_staging=root / "tmp" / "backup",
        backups=root / "backups",
    )


def _database(path: Path, *, title: str = "Story") -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, isolation_level=None)
    apply_migrations(connection, db_path=path)
    connection.execute(
        "INSERT INTO content (id, title, kind) VALUES (?, ?, ?)",
        ("story", title, "audiobook"),
    )
    return connection


def _ready_layout(root: Path) -> AqenoPaths:
    layout = _layout(root)
    create_data_layout(root)
    layout.config.mkdir(parents=True, exist_ok=True)
    (layout.config / "settings.toml").write_text("[volume]\nchild_maximum = 70\n")
    connection = _database(layout.database)
    connection.close()
    return layout


def _rewrite_zip(path: Path, replacements: dict[str, bytes]) -> None:
    temporary = path.with_suffix(".rewritten")
    with zipfile.ZipFile(path) as source, zipfile.ZipFile(temporary, "w") as target:
        for name in source.namelist():
            target.writestr(name, replacements.get(name, source.read(name)))
    temporary.replace(path)


class TestDataVolume:
    def test_valid_marker_mount_and_capacity_are_accepted(self, tmp_path: Path) -> None:
        marker = create_volume_marker(tmp_path)
        create_data_layout(tmp_path)
        usage = Usage(256 * GIB, 100 * GIB, 156 * GIB)

        found, capacity = validate_data_volume(
            tmp_path,
            mount_checker=lambda _path: True,
            writable_checker=lambda _path: True,
            usage=usage,
        )

        assert found == marker
        assert capacity.level is CapacityLevel.HEALTHY

    @pytest.mark.parametrize(
        ("prepare", "expected"),
        [
            (lambda root: None, VolumeProblem.MISSING),
            (lambda root: root.mkdir(), VolumeProblem.NOT_MOUNTED),
        ],
    )
    def test_missing_or_unmounted_data_never_falls_back(
        self, tmp_path: Path, prepare: object, expected: VolumeProblem
    ) -> None:
        root = tmp_path / "aqeno-data"
        prepare(root)  # type: ignore[operator]
        with pytest.raises(VolumeValidationError) as error:
            validate_data_volume(root, mount_checker=lambda _path: False)
        assert error.value.problem is expected

    def test_read_only_volume_is_rejected(self, tmp_path: Path) -> None:
        create_volume_marker(tmp_path)
        with pytest.raises(VolumeValidationError) as error:
            validate_data_volume(
                tmp_path,
                mount_checker=lambda _path: True,
                writable_checker=lambda _path: False,
            )
        assert error.value.problem is VolumeProblem.READ_ONLY

    def test_wrong_marker_and_version_are_rejected(self, tmp_path: Path) -> None:
        (tmp_path / "volume.json").write_text("not-json")
        with pytest.raises(VolumeValidationError) as invalid:
            validate_data_volume(tmp_path, require_mount=False, require_layout=False)
        assert invalid.value.problem is VolumeProblem.MARKER_INVALID

        (tmp_path / "volume.json").write_text(
            json.dumps(
                {
                    "data_format_version": 99,
                    "volume_id": "11111111-1111-1111-1111-111111111111",
                    "created_at": "2026-01-01T00:00:00Z",
                }
            )
        )
        with pytest.raises(VolumeValidationError) as unsupported:
            validate_data_volume(tmp_path, require_mount=False, require_layout=False)
        assert unsupported.value.problem is VolumeProblem.VERSION_UNSUPPORTED

    def test_incomplete_or_symlinked_layout_is_rejected(self, tmp_path: Path) -> None:
        create_volume_marker(tmp_path)
        with pytest.raises(VolumeValidationError) as incomplete:
            validate_data_volume(tmp_path, require_mount=False)
        assert incomplete.value.problem is VolumeProblem.LAYOUT_INVALID

        create_data_layout(tmp_path)
        (tmp_path / "cache/index").rmdir()
        (tmp_path / "cache/index").symlink_to(tmp_path / "cache/artwork", target_is_directory=True)
        with pytest.raises(VolumeValidationError) as linked:
            validate_data_volume(tmp_path, require_mount=False)
        assert linked.value.problem is VolumeProblem.LAYOUT_INVALID

    def test_capacity_levels_and_import_reserve(self, tmp_path: Path) -> None:
        healthy = capacity_status(tmp_path, usage=Usage(100 * GIB, 50 * GIB, 50 * GIB))
        warning = capacity_status(tmp_path, usage=Usage(100 * GIB, 93 * GIB, 7 * GIB))
        critical = capacity_status(tmp_path, usage=Usage(100 * GIB, 98 * GIB, 2 * GIB))

        assert healthy.level is CapacityLevel.HEALTHY
        assert warning.level is CapacityLevel.WARNING
        assert critical.level is CapacityLevel.CRITICAL
        assert healthy.permits(20 * GIB)
        assert not warning.permits(6 * GIB)

        create_volume_marker(tmp_path)
        create_data_layout(tmp_path)
        _marker, critical_volume = validate_data_volume(
            tmp_path,
            require_mount=False,
            usage=Usage(100 * GIB, 98 * GIB, 2 * GIB),
        )
        assert critical_volume.level is CapacityLevel.CRITICAL


class TestSqliteSnapshotAndBackup:
    def test_live_wal_database_snapshot_is_readable_and_consistent(self, tmp_path: Path) -> None:
        source = tmp_path / "live.db"
        connection = _database(source)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("UPDATE content SET title = 'Live title' WHERE id = 'story'")

        snapshot = tmp_path / "snapshot.db"
        schema = sqlite_online_snapshot(source, snapshot)

        restored = sqlite3.connect(snapshot)
        try:
            assert schema == CURRENT_SCHEMA_VERSION
            assert get_schema_version(restored) == CURRENT_SCHEMA_VERSION
            assert restored.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            assert restored.execute("SELECT title FROM content").fetchone() == ("Live title",)
        finally:
            restored.close()
            connection.close()

    def test_state_backup_is_atomic_portable_and_validated(self, tmp_path: Path) -> None:
        layout = _ready_layout(tmp_path / "data")
        layout.original_artwork.mkdir(parents=True, exist_ok=True)
        (layout.original_artwork / "custom.webp").write_bytes(b"artwork")
        destination = layout.backups / "state.aqbackup"

        create_state_backup(layout, destination, aqeno_version="0.1.0")
        validation = validate_state_backup(destination)

        assert validation.valid and validation.compatible
        assert validation.manifest is not None
        assert validation.manifest["media_included"] is False
        with zipfile.ZipFile(destination) as archive:
            assert "state/aqeno.db" in archive.namelist()
            assert "state/config/settings.toml" in archive.namelist()
            assert "state/artwork/original/custom.webp" in archive.namelist()
            assert not any(name.startswith("media/") for name in archive.namelist())

    def test_partial_corrupt_checksum_and_unsupported_backups_are_rejected(
        self, tmp_path: Path
    ) -> None:
        layout = _ready_layout(tmp_path / "data")
        valid = create_state_backup(
            layout, layout.backups / "valid.aqbackup", aqeno_version="0.1.0"
        )

        partial = layout.backups / "interrupted.aqbackup.partial"
        partial.write_bytes(valid.read_bytes())
        assert not validate_state_backup(partial).valid

        corrupt = layout.backups / "corrupt.aqbackup"
        corrupt.write_bytes(b"not a zip archive")
        assert not validate_state_backup(corrupt).valid

        checksum = layout.backups / "checksum.aqbackup"
        checksum.write_bytes(valid.read_bytes())
        with zipfile.ZipFile(checksum) as archive:
            settings_payload = archive.read("state/config/settings.toml")
        changed_payload = b"!" + settings_payload[1:]
        _rewrite_zip(checksum, {"state/config/settings.toml": changed_payload})
        assert "checksum mismatch" in validate_state_backup(checksum).message

        unsupported = layout.backups / "unsupported.aqbackup"
        unsupported.write_bytes(valid.read_bytes())
        with zipfile.ZipFile(unsupported) as archive:
            manifest = json.loads(archive.read("manifest.json"))
        manifest["backup_format_version"] = 99
        _rewrite_zip(
            unsupported,
            {"manifest.json": json.dumps(manifest, sort_keys=True).encode("utf-8")},
        )
        result = validate_state_backup(unsupported)
        assert not result.valid and not result.compatible

    def test_failed_final_backup_activation_leaves_no_visible_or_partial_backup(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        layout = _ready_layout(tmp_path / "data")
        destination = layout.backups / "state.aqbackup"

        real_replace = backup_module.os.replace

        def fail_replace(source: Path, target: Path) -> None:
            if Path(target) == destination:
                raise OSError("simulated power loss")
            real_replace(source, target)

        monkeypatch.setattr(backup_module.os, "replace", fail_replace)
        with pytest.raises(OSError, match="simulated power loss"):
            create_state_backup(layout, destination, aqeno_version="0.1.0")

        assert not destination.exists()
        assert not destination.with_name(destination.name + ".partial").exists()

    def test_backup_capacity_is_rejected_before_staging(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        layout = _ready_layout(tmp_path / "data")
        destination = layout.backups / "state.aqbackup"
        constrained = CapacityStatus(CapacityLevel.CRITICAL, 1000, 10, 100, 50)
        monkeypatch.setattr(backup_module, "capacity_status", lambda _root: constrained)

        with pytest.raises(BackupError, match="insufficient reserved"):
            create_state_backup(layout, destination, aqeno_version="0.1.0")

        assert not destination.exists()
        assert not list(layout.backup_staging.iterdir())


class TestPrototypeMigration:
    def _legacy(self, root: Path) -> tuple[Path, Path]:
        config = root / "etc-aqeno"
        data = root / "var-lib-aqeno"
        config.mkdir()
        (config / "settings.toml").write_text("[display]\nkids_early = 30\n")
        connection = _database(data / "aqeno.db", title="Legacy story")
        connection.close()
        (data / "media").mkdir()
        (data / "media" / "story.mp3").write_bytes(b"audio")
        (data / "artwork").mkdir()
        (data / "artwork" / "story.webp").write_bytes(b"artwork")
        (data / "state").mkdir()
        (data / "state" / "management.key").write_text("legacy-break-glass\n")
        (data / "state" / "device-id").write_text("11111111-1111-1111-1111-111111111111\n")
        return config, data

    def test_clean_migration_and_rerun_preserve_source_and_target(self, tmp_path: Path) -> None:
        config, data = self._legacy(tmp_path)
        layout = _layout(tmp_path / "aqeno-data")
        layout.data_root.mkdir()
        create_data_layout(layout.data_root)

        first = migrate_prototype_data(layout, legacy_config=config, legacy_data=data)
        second = migrate_prototype_data(layout, legacy_config=config, legacy_data=data)

        assert first.source_found and "state/aqeno.db" in first.copied
        assert second.copied == () and "state/aqeno.db" in second.already_present
        assert (layout.media / "story.mp3").read_bytes() == b"audio"
        assert (layout.state / "secrets/management.key").read_text() == "legacy-break-glass\n"
        assert (layout.state / "identity/device-id").read_text().startswith("11111111-")
        assert (data / "media" / "story.mp3").read_bytes() == b"audio"
        migrated = sqlite3.connect(layout.database)
        try:
            assert migrated.execute("SELECT title FROM content").fetchone() == ("Legacy story",)
        finally:
            migrated.close()

    def test_interruption_after_activation_is_safely_resumed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        config, data = self._legacy(tmp_path)
        layout = _layout(tmp_path / "aqeno-data")
        layout.data_root.mkdir()
        create_data_layout(layout.data_root)
        real_write = migration_module._write_json_atomic
        interrupted = False

        def interrupt_once(path: Path, value: dict[str, object]) -> None:
            nonlocal interrupted
            if value.get("state") == "committing" and not interrupted:
                interrupted = True
                raise OSError("simulated power loss")
            real_write(path, value)

        monkeypatch.setattr(migration_module, "_write_json_atomic", interrupt_once)
        with pytest.raises(OSError, match="simulated power loss"):
            migrate_prototype_data(layout, legacy_config=config, legacy_data=data)
        monkeypatch.setattr(migration_module, "_write_json_atomic", real_write)

        resumed = migrate_prototype_data(layout, legacy_config=config, legacy_data=data)

        assert resumed.source_found
        assert layout.database.is_file()
        assert (layout.state / "prototype-migration.json").is_file()

    def test_conflicting_target_stops_without_overwriting(self, tmp_path: Path) -> None:
        config, data = self._legacy(tmp_path)
        layout = _layout(tmp_path / "aqeno-data")
        layout.data_root.mkdir()
        create_data_layout(layout.data_root)
        layout.config.mkdir(parents=True, exist_ok=True)
        target = layout.config / "settings.toml"
        target.write_text("different = true\n")

        with pytest.raises(MigrationConflictError, match="differing state"):
            migrate_prototype_data(layout, legacy_config=config, legacy_data=data)

        assert target.read_text() == "different = true\n"

    def test_absent_prototype_is_a_no_op(self, tmp_path: Path) -> None:
        layout = _layout(tmp_path / "aqeno-data")
        layout.data_root.mkdir()
        result = migrate_prototype_data(
            layout,
            legacy_config=tmp_path / "missing-config",
            legacy_data=tmp_path / "missing-data",
        )
        assert result == migration_module.MigrationResult((), (), False)

    def test_migration_capacity_is_checked_before_staging(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        config, data = self._legacy(tmp_path)
        layout = _layout(tmp_path / "aqeno-data")
        layout.data_root.mkdir()
        create_data_layout(layout.data_root)
        constrained = CapacityStatus(CapacityLevel.CRITICAL, 1000, 10, 100, 50)
        monkeypatch.setattr(migration_module, "capacity_status", lambda _root: constrained)

        with pytest.raises(MigrationConflictError, match="insufficient reserved"):
            migrate_prototype_data(layout, legacy_config=config, legacy_data=data)

        assert not (layout.temporary / "migration").exists()


class TestImportStaging:
    def test_capacity_preflight_rejects_import_before_staging(self, tmp_path: Path) -> None:
        status = CapacityStatus(CapacityLevel.WARNING, 1000, 100, 200, 50)
        assets = LocalAssetStore(
            media_root=tmp_path / "media",
            artwork_root=tmp_path / "artwork",
            import_staging_root=tmp_path / "staging",
            capacity=lambda: status,
        )

        with pytest.raises(InsufficientCapacityError):
            assets.store_media(BytesIO(b"x" * 60), filename="story.mp3")

        assert not (tmp_path / "staging").exists()
        assert not (tmp_path / "media").exists()

    def test_interrupted_staging_never_becomes_published_media(self, tmp_path: Path) -> None:
        staging = tmp_path / "staging"
        interrupted = staging / "operation"
        interrupted.mkdir(parents=True)
        (interrupted / "story.mp3").write_bytes(b"partial")
        assets = LocalAssetStore(
            media_root=tmp_path / "media",
            artwork_root=tmp_path / "artwork",
            import_staging_root=staging,
        )

        assert assets.cleanup_interrupted_imports() == 1
        assert list(staging.iterdir()) == []
        assert not (tmp_path / "media").exists()
