from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from aqeno.adapters.fakes import (
    FakeAudioEngine,
    FakeClock,
    FakeDisplayPanel,
    FakeInputBus,
    FakeLibrary,
    FakeStatusLeds,
)
from aqeno.application.device_ui import DeviceSurface, DeviceUiState
from aqeno.application.display import DisplayService
from aqeno.application.playback import PlaybackSession
from aqeno.application.readiness import Readiness, ReadinessState
from aqeno.config.defaults import default_settings
from aqeno.domain.content import ContentId, ContentItem, ContentKind, HttpSource
from aqeno.domain.display import DisplayEvent, DisplayState
from aqeno.domain.profile import DisplayPolicy, ExperienceLevel, Profile, Role, VolumeLimits
from aqeno.ports.audio import TransportState


def _profile() -> Profile:
    return Profile(
        name="kids-early",
        level=ExperienceLevel.KIDS_EARLY,
        role=Role.USER,
        display=DisplayPolicy(
            inactivity_timeout=timedelta(seconds=30),
            night_timeout=timedelta(seconds=10),
            allows_dim=True,
            dim_hold=timedelta(seconds=10),
            interactive_brightness=70,
            dim_brightness=8,
            ambient_brightness=40,
            night_brightness=5,
            led_brightness=20,
        ),
        volume=VolumeLimits(maximum=70, night_maximum=35, headphone_maximum=55),
    )


def _item(title: str, *, available: bool = True, artwork: Path | None = None) -> ContentItem:
    return ContentItem(
        id=ContentId(),
        title=title,
        kind=ContentKind.AUDIOBOOK,
        sources=(HttpSource(f"https://example.invalid/{title}", seekable=True),),
        duration=timedelta(minutes=5),
        artwork=artwork,
        available=available,
    )


def _state() -> tuple[DeviceUiState, FakeLibrary, PlaybackSession, DisplayService]:
    clock = FakeClock()
    inputs = FakeInputBus()
    library = FakeLibrary()
    playback = PlaybackSession(
        audio=FakeAudioEngine(),
        library=library,
        clock=clock,
        settings=default_settings(),
        inputs=inputs,
    )
    profile = _profile()
    playback.use_profile(profile)
    readiness = Readiness(clock)
    readiness.advance(ReadinessState.LOCAL_READY)
    readiness.advance(ReadinessState.PLAYBACK_READY)
    readiness.advance(ReadinessState.UI_READY)
    display = DisplayService(
        panel=FakeDisplayPanel(),
        leds=FakeStatusLeds(),
        clock=clock,
        readiness=readiness,
        profile=profile,
        settings=default_settings(),
    )
    playback.on_changed(display.handle_playback_changed)
    display.handle_event(DisplayEvent.WAKE_REQUEST)
    state = DeviceUiState(
        library=library,
        playback=playback,
        display=display,
        profile=profile,
    )
    return state, library, playback, display


def test_home_exposes_only_available_content_as_typed_tiles(tmp_path: Path) -> None:
    state, library, _, _ = _state()
    visible = _item("Visible", artwork=tmp_path / "cover.jpg")
    library.save_content(visible)
    library.save_content(_item("Missing", available=False))

    state.refresh_library()

    assert state.snapshot.surface is DeviceSurface.HOME
    assert len(state.snapshot.tiles) == 1
    assert state.snapshot.tiles[0].content_id == visible.id
    assert state.snapshot.tiles[0].artwork == tmp_path / "cover.jpg"


def test_selecting_a_tile_starts_playback_and_switches_surface() -> None:
    state, library, playback, _ = _state()
    item = _item("Story")
    library.save_content(item)
    state.refresh_library()

    assert state.select_content(item.id) is True

    assert state.snapshot.surface is DeviceSurface.NOW_PLAYING
    assert state.snapshot.playback.transport is TransportState.PLAYING
    assert state.snapshot.playback.content_id == item.id

    playback.stop()

    assert state.snapshot.surface is DeviceSurface.HOME


def test_stale_or_unavailable_selection_is_ignored() -> None:
    state, library, _, _ = _state()
    unavailable = _item("Unavailable", available=False)
    library.save_content(unavailable)

    assert state.select_content(ContentId()) is False
    assert state.select_content(unavailable.id) is False
    assert state.snapshot.surface is DeviceSurface.HOME


def test_display_and_playback_changes_publish_one_immutable_shape() -> None:
    state, library, _, display = _state()
    item = _item("Story")
    library.save_content(item)
    state.refresh_library()
    received = []
    state.on_changed(received.append)

    state.select_content(item.id)
    display.handle_event(DisplayEvent.INACTIVITY_ELAPSED)

    assert received[-1].surface is DeviceSurface.NOW_PLAYING
    assert received[-1].display.state is DisplayState.DIM
    assert received[-1].playback.content_id == item.id
