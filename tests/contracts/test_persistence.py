"""Contract suite for the persistence port — ADR 0007, ADR 0008 § 3.

Runs against both implementations of `Library` (SQLite, `FakeLibrary`) and both
implementations of `SettingsStore` (TOML, `FakeSettingsStore`). This is the
suite that stops the fakes from drifting away from what the real adapters
actually do — a fixture is parametrised, not the assertions duplicated.
"""

from __future__ import annotations

from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
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
    Fingerprint,
    HttpSource,
    LocalFileSource,
    MemberFile,
    ReplayGain,
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


def _member_file(
    path: str, *, ordinal: int = 0, size_bytes: int = 1000, digest: bytes = b"\x01" * 16
) -> MemberFile:
    return MemberFile(
        path=Path(path),
        ordinal=ordinal,
        size_bytes=size_bytes,
        mtime=1234.5,
        fingerprint=Fingerprint(size_bytes=size_bytes, digest=digest),
        replaygain=ReplayGain(
            track_gain_db=-6.5, track_peak=0.98, album_gain_db=-7.0, album_peak=0.99
        ),
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


class TestScanFields:
    """CONTENT_INGESTION.md § 11: availability, last-seen and the inference rule."""

    def test_round_trips_availability_last_seen_and_inference_rule(self, library: Library) -> None:
        item = replace(
            _content(),
            available=False,
            last_seen=123.5,
            kind_inference_rule="rule-8-ambiguity-default",
        )
        library.save_content(item)
        got = library.get_content(item.id)
        assert got is not None
        assert got.available is False
        assert got.last_seen == 123.5
        assert got.kind_inference_rule == "rule-8-ambiguity-default"

    def test_defaults_to_available_with_no_inference_rule(self, library: Library) -> None:
        library.save_content(_content())
        item = library.list_content()[0]
        assert item.available is True
        assert item.last_seen is None
        assert item.kind_inference_rule is None


class TestMemberFiles:
    """CONTENT_INGESTION.md § 11: the fingerprint index a rescan resolves identity
    against, and the scan-oriented `save_content()` path."""

    def test_omitting_member_files_leaves_previously_stored_ones_untouched(
        self, library: Library
    ) -> None:
        item = _content()
        member = _member_file("/media/a.mp3")
        library.save_content(item, member_files=(member,))

        library.save_content(item)  # ordinary save, no member_files given

        assert library.get_member_files(item.id) == (member,)

    def test_giving_member_files_replaces_the_stored_set(self, library: Library) -> None:
        item = _content()
        library.save_content(item, member_files=(_member_file("/media/old.mp3"),))

        new_member = _member_file("/media/new.mp3", digest=b"\x02" * 16)
        library.save_content(item, member_files=(new_member,))

        assert library.get_member_files(item.id) == (new_member,)

    def test_unknown_content_has_no_member_files(self, library: Library) -> None:
        assert library.get_member_files(ContentId()) == ()

    def test_find_by_fingerprint_locates_the_owning_work(self, library: Library) -> None:
        item = _content()
        member = _member_file("/media/a.mp3", digest=b"\x03" * 16)
        library.save_content(item, member_files=(member,))

        assert library.find_by_fingerprint(member.fingerprint) == item.id

    def test_find_by_fingerprint_is_none_when_unknown(self, library: Library) -> None:
        unknown = Fingerprint(size_bytes=42, digest=b"\x09" * 16)
        assert library.find_by_fingerprint(unknown) is None

    def test_removing_content_cascades_to_its_member_files(self, library: Library) -> None:
        item = _content()
        member = _member_file("/media/a.mp3", digest=b"\x04" * 16)
        library.save_content(item, member_files=(member,))

        library.remove_content(item.id)

        assert library.get_member_files(item.id) == ()
        assert library.find_by_fingerprint(member.fingerprint) is None


class TestMarkUnavailable:
    def test_marks_listed_works_unavailable_without_touching_others(self, library: Library) -> None:
        gone, stays = _content("Gone"), _content("Stays")
        library.save_content(gone)
        library.save_content(stays)

        library.mark_unavailable((gone.id,))

        got_gone = library.get_content(gone.id)
        got_stays = library.get_content(stays.id)
        assert got_gone is not None and got_gone.available is False
        assert got_stays is not None and got_stays.available is True

    def test_preserves_resume_position_and_tag_mapping(self, library: Library) -> None:
        item = _content()
        library.save_content(item)
        library.map_tag("uid-1", item.id)
        library.set_resume(item.id, "kids-early", timedelta(seconds=42))

        library.mark_unavailable((item.id,))

        assert library.resolve_tag("uid-1") == item.id
        assert library.get_resume(item.id, "kids-early") == timedelta(seconds=42)

    def test_empty_tuple_marks_nothing(self, library: Library) -> None:
        item = _content()
        library.save_content(item)
        library.mark_unavailable(())
        got = library.get_content(item.id)
        assert got is not None
        assert got.available is True


def test_resume_access_from_adapter_callback_thread(library: Library) -> None:
    item = _content("Threaded resume")
    profile = _profile("threaded-profile")
    library.save_content(item)
    library.save_profile(profile)

    def write_and_read() -> timedelta | None:
        library.set_resume(item.id, profile.name, timedelta(seconds=42))
        return library.get_resume(item.id, profile.name)

    with ThreadPoolExecutor(max_workers=1) as executor:
        assert executor.submit(write_and_read).result(timeout=2) == timedelta(seconds=42)


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
