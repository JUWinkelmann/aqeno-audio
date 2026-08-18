"""Storage locations honour `AQENO_*_DIR` — ADR 0007 § 4.

Tests must never touch real device state; this confirms the override the
`aqeno_state_dirs` fixture relies on actually works, for the paths and for the
adapters that default to them.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from aqeno.adapters.persistence import TomlSettingsStore, open_library
from aqeno.config import paths


def test_env_overrides_are_used_directly(aqeno_state_dirs: Path) -> None:
    assert paths.config_dir() == aqeno_state_dirs / "aqeno_config_dir"
    assert paths.data_dir() == aqeno_state_dirs / "aqeno_data_dir"
    assert paths.state_dir() == aqeno_state_dirs / "aqeno_state_dir"


def test_settings_and_database_paths_are_under_the_overrides(aqeno_state_dirs: Path) -> None:
    assert paths.settings_path() == aqeno_state_dirs / "aqeno_config_dir" / "settings.toml"
    assert paths.database_path() == aqeno_state_dirs / "aqeno_data_dir" / "aqeno.db"


def test_open_library_with_no_argument_uses_the_overridden_data_dir(
    aqeno_state_dirs: Path,
) -> None:
    library = open_library()
    try:
        db_path = aqeno_state_dirs / "aqeno_data_dir" / "aqeno.db"
        assert db_path.exists()
    finally:
        library.close()


def test_toml_settings_store_with_no_argument_uses_the_overridden_config_dir(
    aqeno_state_dirs: Path,
) -> None:
    store = TomlSettingsStore()
    store.save(store.load())
    settings_path = aqeno_state_dirs / "aqeno_config_dir" / "settings.toml"
    assert settings_path.exists()


def test_appliance_paths_derive_every_writable_location_from_data_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_root = tmp_path / "aqeno-data"
    monkeypatch.setenv("AQENO_APPLIANCE", "1")
    monkeypatch.setenv("AQENO_DATA_ROOT", str(data_root))
    for name in ("AQENO_CONFIG_DIR", "AQENO_DATA_DIR", "AQENO_STATE_DIR", "AQENO_MEDIA_DIR"):
        monkeypatch.delenv(name, raising=False)

    layout = paths.paths()

    assert layout.application_root == Path("/opt/aqeno")
    for writable in (
        layout.config,
        layout.database,
        layout.state,
        layout.media,
        layout.original_artwork,
        layout.derived_artwork,
        layout.cache,
        layout.temporary,
        layout.import_staging,
        layout.backup_staging,
        layout.backups,
    ):
        assert writable.is_relative_to(data_root)


def test_appliance_mode_rejects_legacy_path_overrides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AQENO_APPLIANCE", "true")
    monkeypatch.setenv("AQENO_DATA_ROOT", str(tmp_path / "aqeno-data"))
    monkeypatch.setenv("AQENO_STATE_DIR", str(tmp_path / "unsafe-system-fallback"))

    with pytest.raises(paths.AppliancePathError, match="AQENO_STATE_DIR"):
        paths.paths()
