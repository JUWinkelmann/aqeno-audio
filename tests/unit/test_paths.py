"""Storage locations honour `AQENO_*_DIR` — ADR 0007 § 4.

Tests must never touch real device state; this confirms the override the
`aqeno_state_dirs` fixture relies on actually works, for the paths and for the
adapters that default to them.
"""

from __future__ import annotations

from pathlib import Path

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
