from __future__ import annotations

from collections.abc import Iterator
from datetime import timedelta
from pathlib import Path

import pytest

from aqeno.adapters.fakes.persistence import FakeLibrary
from aqeno.adapters.persistence import open_library
from aqeno.application.management import ProfileContentManagement
from aqeno.domain.access import (
    AccessDecision,
    AccessSource,
    Audience,
    AudienceMode,
    Collection,
    CollectionId,
)
from aqeno.domain.content import ContentId, ContentItem, ContentKind, LocalFileSource
from aqeno.domain.profile import DisplayPolicy, ExperienceLevel, Profile, Role, VolumeLimits
from aqeno.ports.persistence import ContentQuery, Library


def _profile(name: str) -> Profile:
    return Profile(
        name=name,
        level=ExperienceLevel.STANDARD,
        role=Role.USER,
        display=DisplayPolicy(
            inactivity_timeout=timedelta(seconds=60),
            night_timeout=timedelta(seconds=15),
            allows_dim=True,
            dim_hold=timedelta(seconds=10),
            interactive_brightness=70,
            dim_brightness=15,
            ambient_brightness=20,
            night_brightness=5,
            led_brightness=15,
        ),
        volume=VolumeLimits(maximum=80, night_maximum=40, headphone_maximum=60),
    )


def _content(title: str) -> ContentItem:
    return ContentItem(
        id=ContentId(),
        title=title,
        kind=ContentKind.AUDIOBOOK,
        sources=(LocalFileSource(Path(f"/media/{title}.mp3")),),
    )


@pytest.fixture(params=["sqlite", "fake"])
def library(request: pytest.FixtureRequest, tmp_path: Path) -> Iterator[Library]:
    result: Library = (
        open_library(tmp_path / "data") if request.param == "sqlite" else FakeLibrary()
    )
    yield result
    result.close()


def _seed(library: Library) -> tuple[ProfileContentManagement, ContentItem]:
    library.save_profile(_profile("anna"))
    library.save_profile(_profile("paul"))
    item = _content("Shared story")
    library.save_content(item)
    return ProfileContentManagement(library), item


def test_favorites_and_progress_are_independent_per_profile(library: Library) -> None:
    access, item = _seed(library)
    access.set_favorite("anna", item.id, True)
    library.set_resume(item.id, "anna", timedelta(minutes=4))
    library.set_resume(item.id, "paul", timedelta(minutes=9))

    assert library.is_favorite("anna", item.id)
    assert not library.is_favorite("paul", item.id)
    assert library.get_resume(item.id, "anna") == timedelta(minutes=4)
    assert library.get_resume(item.id, "paul") == timedelta(minutes=9)


def test_shared_default_and_selected_audience_cover_many_profiles(library: Library) -> None:
    access, item = _seed(library)
    assert access.effective(item.id, "anna").allowed
    assert access.effective(item.id, "paul").allowed

    access.set_audience((item.id,), Audience(AudienceMode.SELECTED_PROFILES, ("anna",)))
    assert access.effective(item.id, "anna").allowed
    assert not access.effective(item.id, "paul").allowed


def test_collection_inheritance_and_media_override_have_deterministic_precedence(
    library: Library,
) -> None:
    access, item = _seed(library)
    access.set_audience((item.id,), Audience(AudienceMode.SELECTED_PROFILES, ()))
    collection = Collection(CollectionId(), "Stories", (item.id,))
    access.save_collection(collection)
    access.set_collection_audience(
        collection.id, Audience(AudienceMode.SELECTED_PROFILES, ("anna", "paul"))
    )

    inherited = access.effective(item.id, "anna")
    assert inherited.allowed and inherited.source is AccessSource.COLLECTION

    access.set_overrides((item.id,), ("anna",), AccessDecision.DENY)
    denied = access.effective(item.id, "anna")
    assert not denied.allowed and denied.source is AccessSource.MEDIA_OVERRIDE
    assert access.effective(item.id, "paul").allowed

    access.set_overrides((item.id,), ("anna",), None)
    assert access.effective(item.id, "anna").allowed


def test_profile_library_filter_is_server_side_and_new_profiles_inherit_shared(
    library: Library,
) -> None:
    access, shared = _seed(library)
    private = _content("Anna only")
    library.save_content(private)
    access.set_audience((private.id,), Audience(AudienceMode.SELECTED_PROFILES, ("anna",)))
    library.save_profile(_profile("new-profile"))

    anna = library.query_content(ContentQuery(limit=100, profile_name="anna"))
    paul = library.query_content(ContentQuery(limit=100, profile_name="paul"))
    newcomer = library.query_content(ContentQuery(limit=100, profile_name="new-profile"))
    assert {item.id for item in anna.items} == {shared.id, private.id}
    assert {item.id for item in paul.items} == {shared.id}
    assert {item.id for item in newcomer.items} == {shared.id}


def test_bulk_mutation_updates_hundreds_of_media_for_multiple_profiles(library: Library) -> None:
    library.save_profile(_profile("anna"))
    library.save_profile(_profile("paul"))
    items = tuple(_content(f"Item {index:03}") for index in range(300))
    for item in items:
        library.save_content(item)
    access = ProfileContentManagement(library)

    access.set_audience(
        tuple(item.id for item in items),
        Audience(AudienceMode.SELECTED_PROFILES, ("anna", "paul")),
    )

    assert library.query_content(ContentQuery(limit=100, profile_name="anna")).total == 300
    assert library.query_content(ContentQuery(limit=100, profile_name="paul")).total == 300
