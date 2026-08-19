"""Presentation levels change density; design targets stay out of the product.

Two rules that are easy to erode and hard to notice once eroded: a presentation
level must never become a second interaction architecture, and a drawn screen
must never become an available capability.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from aqeno.adapters.fakes import (
    FakeAudioEngine,
    FakeClock,
    FakeDisplayPanel,
    FakeInputBus,
    FakeLibrary,
    FakeStatusLeds,
)
from aqeno.application.device_ui import DeviceSurface, DeviceUiState, PresentationLevel
from aqeno.application.display import DisplayService
from aqeno.application.playback import PlaybackSession
from aqeno.application.readiness import Readiness, ReadinessState
from aqeno.config.defaults import default_settings
from aqeno.domain.content import ContentId, ContentItem, ContentKind, HttpSource
from aqeno.domain.display import DisplayEvent
from aqeno.domain.profile import (
    DisplayPolicy,
    ExperienceLevel,
    Profile,
    Role,
    VolumeLimits,
)
from aqeno.ports.input import FocusNext, Home, Select

QML_DIR = Path("src/aqeno/ui/qml")
PREVIEW_DIR = Path("scripts/ui_preview")


def _profile(level: ExperienceLevel) -> Profile:
    return Profile(
        name="test",
        level=level,
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


def _state(level: ExperienceLevel) -> DeviceUiState:
    clock = FakeClock()
    library = FakeLibrary()
    for title in ("One", "Two"):
        library.save_content(
            ContentItem(
                id=ContentId(),
                title=title,
                kind=ContentKind.AUDIOBOOK,
                sources=(HttpSource(f"https://example.invalid/{title}", seekable=True),),
                duration=timedelta(minutes=5),
            )
        )
    profile = _profile(level)
    playback = PlaybackSession(
        audio=FakeAudioEngine(),
        library=library,
        clock=clock,
        settings=default_settings(),
        inputs=FakeInputBus(),
    )
    playback.use_profile(profile)
    readiness = Readiness(clock)
    for rung in (
        ReadinessState.LOCAL_READY,
        ReadinessState.PLAYBACK_READY,
        ReadinessState.UI_READY,
    ):
        readiness.advance(rung)
    display = DisplayService(
        panel=FakeDisplayPanel(),
        leds=FakeStatusLeds(),
        clock=clock,
        readiness=readiness,
        profile=profile,
        settings=default_settings(),
    )
    display.handle_event(DisplayEvent.WAKE_REQUEST)
    state = DeviceUiState(library=library, playback=playback, display=display, profile=profile)
    state.refresh_library()
    return state


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        (ExperienceLevel.KIDS_EARLY, PresentationLevel.VISUAL_LABEL),
        (ExperienceLevel.EASY, PresentationLevel.VISUAL_LABEL),
        (ExperienceLevel.STANDARD, PresentationLevel.INFORMATIVE),
    ],
)
def test_experience_level_maps_onto_one_presentation_axis(
    level: ExperienceLevel, expected: PresentationLevel
) -> None:
    assert _state(level).snapshot.presentation_level is expected


def test_presentation_level_changes_nothing_a_person_can_do() -> None:
    """Density only. Navigation, focus and what a press starts are identical."""
    journeys = {}
    for level in (ExperienceLevel.KIDS_EARLY, ExperienceLevel.STANDARD):
        state = _state(level)
        steps = []
        state.handle_navigation(Select())
        steps.append((state.snapshot.surface, state.snapshot.open_section_key))
        state.handle_navigation(FocusNext())
        steps.append((state.snapshot.surface, state.snapshot.focused_content_id))
        state.handle_navigation(Select())
        steps.append((state.snapshot.surface, state.snapshot.playback.content_id))
        state.handle_navigation(Home())
        steps.append((state.snapshot.surface, state.snapshot.open_section_key))
        # Content ids differ per instance; compare the shape of the journey.
        journeys[level] = [
            (surface, value is not None if value is not None else None)
            if not isinstance(value, str)
            else (surface, value)
            for surface, value in steps
        ]

    assert journeys[ExperienceLevel.KIDS_EARLY] == journeys[ExperienceLevel.STANDARD]
    assert journeys[ExperienceLevel.STANDARD][-1][0] is DeviceSurface.HOME


def test_a_level_is_a_presentation_value_not_a_capability_switch() -> None:
    """Every level is reachable on the same snapshot without touching anything
    else — a level can never gate a function."""
    snapshot = _state(ExperienceLevel.KIDS_EARLY).snapshot
    for level in PresentationLevel:
        altered = replace(snapshot, presentation_level=level)
        assert altered.sections == snapshot.sections
        assert altered.tiles == snapshot.tiles
        assert altered.surface is snapshot.surface


def test_design_targets_are_unreachable_from_the_product_surface() -> None:
    """A visual target does not make a capability available (P15)."""
    product = "\n".join(path.read_text() for path in QML_DIR.glob("*.qml"))

    assert "ui_preview" not in product
    for target in ("Clock", "Timer", "Alarm", "Message", "ContextActions"):
        assert f"{target}Screen" not in product, f"{target} is routed into the product"


def test_preview_qml_holds_presentation_state_only() -> None:
    """No repository, service, controller or store reaches a design target."""
    forbidden = ("aqeno.", "import Qt.labs", "XMLHttpRequest", "Qt.createComponent")
    for path in PREVIEW_DIR.glob("*.qml"):
        source = path.read_text()
        for token in forbidden:
            assert token not in source, f"{path.name} reaches beyond presentation: {token}"


def test_timer_and_alarm_targets_decide_no_open_interaction_question() -> None:
    """C1 (snooze) and C2 (cancelling a running timer blind) stay open, so no
    drawn label may answer them."""
    labels = ("Snooze", "snooze", "Stopp", "Abbrechen", "Beenden", "Weiter schlafen")
    for name in (
        "AlarmRingingScreen.qml",
        "TimerRunningScreen.qml",
        "TimerFinishedScreen.qml",
    ):
        source = (PREVIEW_DIR / name).read_text()
        for label in labels:
            assert f'qsTr("{label}' not in source, f"{name} settles an open question"
