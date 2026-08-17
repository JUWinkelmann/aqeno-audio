"""`TomlSettingsStore` — ADR 0007 § "Settings".

The settings file is untrusted, hand-editable input. `load()` must never raise
and must never rewrite a file it merely read from; `save()` must write
atomically.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from aqeno.adapters.persistence.toml_settings import TomlSettingsStore
from aqeno.config.defaults import default_settings


class TestMissingOrUnreadableFile:
    def test_missing_file_yields_defaults(self, tmp_path: Path) -> None:
        store = TomlSettingsStore(tmp_path / "settings.toml")
        assert store.load() == default_settings()

    def test_unreadable_file_yields_defaults_and_is_untouched(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.toml"
        path.write_text('language = "de"\n')
        original_mode = path.stat().st_mode
        path.chmod(0o000)
        try:
            store = TomlSettingsStore(path)
            settings = store.load()
        finally:
            path.chmod(original_mode)
        assert settings == default_settings()


class TestMalformedFileNeverPreventsStartup:
    def test_invalid_toml_syntax_yields_defaults(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.toml"
        path.write_text("this is not [ valid toml")
        store = TomlSettingsStore(path)
        assert store.load() == default_settings()

    def test_invalid_toml_syntax_is_left_on_disk(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.toml"
        original = "this is not [ valid toml"
        path.write_text(original)
        TomlSettingsStore(path).load()
        assert path.read_text() == original

    def test_out_of_range_value_is_clamped_and_file_left_alone(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.toml"
        original = "[volume]\nchild_maximum = 999\n"
        path.write_text(original)
        store = TomlSettingsStore(path)

        settings = store.load()

        assert settings.volume.child_maximum == 70
        assert path.read_text() == original, "load() must never rewrite the file"

    def test_wrong_type_falls_back_and_rest_of_file_still_loads(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.toml"
        path.write_text('language = "de"\n[nfc]\ndebounce_ms = "soon"\n')
        settings = TomlSettingsStore(path).load()
        assert settings.language == "de"
        assert settings.nfc.debounce_ms == default_settings().nfc.debounce_ms


class TestAtomicWrite:
    def test_save_then_load_round_trips(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.toml"
        store = TomlSettingsStore(path)
        custom = replace(default_settings(), language="de")

        store.save(custom)

        assert TomlSettingsStore(path).load() == custom

    def test_save_leaves_no_temp_file_behind(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.toml"
        TomlSettingsStore(path).save(default_settings())
        assert list(tmp_path.iterdir()) == [path]

    def test_save_creates_missing_parent_directory(self, tmp_path: Path) -> None:
        path = tmp_path / "nested" / "settings.toml"
        TomlSettingsStore(path).save(default_settings())
        assert path.exists()

    def test_save_replaces_rather_than_appends(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.toml"
        store = TomlSettingsStore(path)
        store.save(replace(default_settings(), language="de"))
        store.save(replace(default_settings(), language="en"))
        assert TomlSettingsStore(path).load().language == "en"
        assert path.read_text().count("language =") == 1
