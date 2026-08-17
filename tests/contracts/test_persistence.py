"""Contract suite for the persistence port — ADR 0007, ADR 0008 § 3.

Runs against both implementations of `Library` (SQLite, `FakeLibrary`) and both
implementations of `SettingsStore` (TOML, `FakeSettingsStore`). This is the
suite that stops the fakes from drifting away from what the real adapters
actually do — a fixture is parametrised, not the assertions duplicated.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from aqeno.adapters.fakes.persistence import FakeLibrary, FakeSettingsStore
from aqeno.adapters.persistence import TomlSettingsStore, open_library
from aqeno.config.defaults import default_settings
from aqeno.domain.content import (
    Chapter,
    ContentId,
    ContentItem,
    ContentKind,
    HttpSource,
    LocalFileSource,
)
from aqeno.domain.profile import DisplayPolicy, ExperienceLevel, Profile, Role, VolumeLimits
from aqeno.ports.persistence import DatabaseHealth, Library, SettingsStore, UnknownContentError


def _content(title: str = "Item") -> ContentItem:
    return ContentItem(
        id=ContentId(),
        title=title,
        kind=ContentKind.AUDIOBOOK,
        sources=(
            LocalFileSource(path=Path(f"/media/{title}.mp3")),
            HttpSource(url=f"https://example.invalid/{title}", seekable=True),
        ),
        chapters=(
            Chapter(index=0, title="Chapter 1", start=timedelta(0), duration=timedelta(minutes=5)),
            Chapter(index=1, title="Chapter 2", start=timedelta(minutes=5), duration=None),
        ),
        duration=timedelta(minutes=10),
        artwork=Path(f"/art/{title}.jpg"),
        language="de",
    )


def _profile(name: str = "kids-early") -> Profile:
    return Profile(
        name=name,
        level=ExperienceLevel.KIDS_EARLY,
        role=Role.USER,
        display=DisplayPolicy(
            inactivity_timeout=timedelta(seconds=30),
            night_timeout=timedelta(seconds=10),
            allows_dim=False,
            dim_hold=None,
            interactive_brightness=70,
            dim_brightness=0,
            ambient_brightness=40,
            night_brightness=5,
            led_brightness=20,
        ),
        volume=VolumeLimits(maximum=70, night_maximum=35, headphone_maximum=55),
    )


@pytest.fixture(params=["sqlite", "fake"])
def library(request: pytest.FixtureRequest, tmp_path: Path) -> Iterator[Library]:
    lib: Library = open_library(tmp_path / "data") if request.param == "sqlite" else FakeLibrary()
    yield lib
    lib.close()


class TestContent:
    def test_round_trips_every_field(self, library: Library) -> None:
        item = _content()
        library.save_content(item)
        assert library.get_content(item.id) == item

    def test_unknown_id_is_none(self, library: Library) -> None:
        assert library.get_content(ContentId()) is None

    def test_list_includes_every_saved_item(self, library: Library) -> None:
        a, b = _content("A"), _content("B")
        library.save_content(a)
        library.save_content(b)
        assert {item.id for item in library.list_content()} == {a.id, b.id}

    def test_saving_again_replaces_sources_and_chapters(self, library: Library) -> None:
        item = _content()
        library.save_content(item)
        updated = replace(item, title="Renamed", chapters=(), sources=item.sources[:1])
        library.save_content(updated)
        got = library.get_content(item.id)
        assert got is not None
        assert got.title == "Renamed"
        assert got.chapters == ()
        assert got.sources == item.sources[:1]


class TestTagMappings:
    """DOMAIN_MODEL.md invariant: deleting/replacing a tag must not delete content."""

    def test_map_then_resolve(self, library: Library) -> None:
        item = _content()
        library.save_content(item)
        library.map_tag("uid-1", item.id)
        assert library.resolve_tag("uid-1") == item.id

    def test_unknown_uid_resolves_to_none(self, library: Library) -> None:
        assert library.resolve_tag("does-not-exist") is None

    def test_mapping_nonexistent_content_is_rejected(self, library: Library) -> None:
        with pytest.raises(UnknownContentError):
            library.map_tag("uid-1", ContentId())

    def test_deleting_a_mapping_does_not_delete_content(self, library: Library) -> None:
        item = _content()
        library.save_content(item)
        library.map_tag("uid-1", item.id)

        library.unmap_tag("uid-1")

        assert library.resolve_tag("uid-1") is None
        assert library.get_content(item.id) == item

    def test_removing_content_cascades_to_its_mapping(self, library: Library) -> None:
        item = _content()
        library.save_content(item)
        library.map_tag("uid-1", item.id)

        library.remove_content(item.id)

        assert library.resolve_tag("uid-1") is None

    def test_lists_every_tag_mapping(self, library: Library) -> None:
        item = _content()
        library.save_content(item)
        library.map_tag("uid-1", item.id)
        mappings = library.list_tags()
        assert [(m.uid, m.content_id) for m in mappings] == [("uid-1", item.id)]


class TestProfiles:
    def test_save_then_get(self, library: Library) -> None:
        profile = _profile()
        library.save_profile(profile)
        assert library.get_profile(profile.name) == profile

    def test_unknown_name_is_none(self, library: Library) -> None:
        assert library.get_profile("nobody") is None

    def test_lists_every_saved_profile(self, library: Library) -> None:
        library.save_profile(_profile("a"))
        library.save_profile(_profile("b"))
        assert {p.name for p in library.list_profiles()} == {"a", "b"}

    def test_save_replaces_by_name(self, library: Library) -> None:
        library.save_profile(_profile("a"))
        updated = replace(_profile("a"), ambient_enabled=True)
        library.save_profile(updated)
        got = library.get_profile("a")
        assert got is not None
        assert got.ambient_enabled is True


class TestResume:
    """CONFIGURATION_DEFAULTS.md § 4."""

    def test_unset_is_none(self, library: Library) -> None:
        item = _content()
        library.save_content(item)
        assert library.get_resume(item.id, "kids-early") is None

    def test_set_then_get(self, library: Library) -> None:
        item = _content()
        library.save_content(item)
        library.set_resume(item.id, "kids-early", timedelta(seconds=42))
        assert library.get_resume(item.id, "kids-early") == timedelta(seconds=42)

    def test_scoped_by_profile(self, library: Library) -> None:
        item = _content()
        library.save_content(item)
        library.set_resume(item.id, "kids-early", timedelta(seconds=10))
        assert library.get_resume(item.id, "someone-else") is None

    def test_write_skipped_when_position_has_not_advanced(self, library: Library) -> None:
        """Paused playback writes nothing — the position must never move backwards
        just because the last write raced a rewind."""
        item = _content()
        library.save_content(item)
        library.set_resume(item.id, "p", timedelta(seconds=30))
        library.set_resume(item.id, "p", timedelta(seconds=10))
        assert library.get_resume(item.id, "p") == timedelta(seconds=30)

    def test_equal_position_is_also_skipped(self, library: Library) -> None:
        item = _content()
        library.save_content(item)
        library.set_resume(item.id, "p", timedelta(seconds=30))
        library.set_resume(item.id, "p", timedelta(seconds=30))
        assert library.get_resume(item.id, "p") == timedelta(seconds=30)

    def test_removing_content_cascades_to_resume(self, library: Library) -> None:
        item = _content()
        library.save_content(item)
        library.set_resume(item.id, "p", timedelta(seconds=5))
        library.remove_content(item.id)
        assert library.get_resume(item.id, "p") is None


class TestHealth:
    def test_fresh_store_is_healthy(self, library: Library) -> None:
        assert library.health() is DatabaseHealth.OK


# ---------------------------------------------------------------------------
# Settings store
# ---------------------------------------------------------------------------


@pytest.fixture(params=["toml", "fake"])
def settings_store(request: pytest.FixtureRequest, tmp_path: Path) -> SettingsStore:
    if request.param == "toml":
        return TomlSettingsStore(tmp_path / "settings.toml")
    return FakeSettingsStore()


class TestSettingsStore:
    def test_first_load_is_defaults(self, settings_store: SettingsStore) -> None:
        assert settings_store.load() == default_settings()

    def test_save_then_load_round_trips(self, settings_store: SettingsStore) -> None:
        custom = replace(default_settings(), language="de")
        settings_store.save(custom)
        assert settings_store.load() == custom

    def test_save_persists_nested_sections(self, settings_store: SettingsStore) -> None:
        base = default_settings()
        custom = replace(base, volume=replace(base.volume, child_maximum=60))
        settings_store.save(custom)
        assert settings_store.load().volume.child_maximum == 60
