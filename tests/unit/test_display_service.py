"""Named tests for `DISPLAY_STATE_MACHINE.md`'s ten invariants, at the level where
timers and output actually live: `application/display.py`. `test_display_state_machine.py`
already proves `domain.display.resolve()` is correct in isolation; these tests prove
the service applies what it resolves — the panel and LED calls a fake records.
"""

from __future__ import annotations

import logging
from datetime import timedelta

import pytest

from aqeno.adapters.fakes import FakeClock, FakeDisplayPanel, FakeStatusLeds
from aqeno.application.display import DisplayService
from aqeno.application.playback import PlaybackSnapshot
from aqeno.application.readiness import Readiness, ReadinessState
from aqeno.config.defaults import Settings, default_settings
from aqeno.domain.content import ContentId
from aqeno.domain.display import DisplayEvent, DisplayState
from aqeno.domain.profile import DisplayPolicy, ExperienceLevel, Profile, Role, VolumeLimits
from aqeno.ports.audio import TransportState

INTERACTIVE_BRIGHTNESS = 70
DIM_BRIGHTNESS = 10
AMBIENT_BRIGHTNESS = 40
NIGHT_MINIMUM = 5
LED_NORMAL = 20


def _profile(
    *,
    role: Role = Role.USER,
    allows_dim: bool = False,
    dim_hold: timedelta | None = None,
    ambient_enabled: bool = False,
    inactivity_timeout: timedelta = timedelta(seconds=30),
    night_timeout: timedelta = timedelta(seconds=10),
) -> Profile:
    return Profile(
        name="test-profile",
        level=ExperienceLevel.STANDARD if allows_dim else ExperienceLevel.KIDS_EARLY,
        role=role,
        display=DisplayPolicy(
            inactivity_timeout=inactivity_timeout,
            night_timeout=night_timeout,
            allows_dim=allows_dim,
            dim_hold=dim_hold,
            interactive_brightness=INTERACTIVE_BRIGHTNESS,
            dim_brightness=DIM_BRIGHTNESS,
            ambient_brightness=AMBIENT_BRIGHTNESS,
            night_brightness=NIGHT_MINIMUM,
            led_brightness=LED_NORMAL,
        ),
        volume=VolumeLimits(
            maximum=100 if allows_dim else 70, night_maximum=35, headphone_maximum=55
        ),
        ambient_enabled=ambient_enabled,
    )


def _playing() -> PlaybackSnapshot:
    return PlaybackSnapshot(
        transport=TransportState.PLAYING,
        content_id=ContentId(),
        title="Test item",
        chapter_title=None,
        position=timedelta(0),
        duration=None,
        volume=40,
        failure_code=None,
        can_toggle_playback=True,
        can_skip_forward=False,
        can_skip_back=False,
    )


def _stopped() -> PlaybackSnapshot:
    return PlaybackSnapshot(
        transport=TransportState.STOPPED,
        content_id=None,
        title=None,
        chapter_title=None,
        position=None,
        duration=None,
        volume=40,
        failure_code=None,
        can_toggle_playback=False,
        can_skip_forward=False,
        can_skip_back=False,
    )


def _service(
    *,
    profile: Profile | None = None,
    settings: Settings | None = None,
    clock: FakeClock | None = None,
    panel: FakeDisplayPanel | None = None,
    leds: FakeStatusLeds | None = None,
    ui_ready: bool = True,
) -> tuple[DisplayService, FakeDisplayPanel, FakeStatusLeds, FakeClock, Readiness]:
    clock = clock if clock is not None else FakeClock()
    readiness = Readiness(clock)
    if ui_ready:
        readiness.advance(ReadinessState.LOCAL_READY)
        readiness.advance(ReadinessState.PLAYBACK_READY)
        readiness.advance(ReadinessState.UI_READY)
    panel = panel if panel is not None else FakeDisplayPanel()
    leds = leds if leds is not None else FakeStatusLeds()
    service = DisplayService(
        panel=panel,
        leds=leds,
        clock=clock,
        readiness=readiness,
        profile=profile if profile is not None else _profile(),
        settings=settings if settings is not None else default_settings(),
    )
    return service, panel, leds, clock, readiness


class TestOffAtStartup:
    """Invariant 9: OFF means no intended visible output, from process start."""

    def test_construction_leaves_the_panel_off_and_leds_off(self) -> None:
        service, panel, leds, _, _ = _service()
        assert service.snapshot.state is DisplayState.OFF
        assert panel.calls == [("power", False)]
        assert leds.calls == [0]


class TestNoFlashOnOff:
    """Invariant 5: entering OFF produces no flash, fade-up or farewell animation —
    exactly one power call, never a brightness call."""

    def test_inactivity_from_interactive_calls_power_off_only(self) -> None:
        service, panel, _, _, _ = _service()
        service.handle_event(DisplayEvent.WAKE_REQUEST)
        panel.calls.clear()

        service.handle_event(DisplayEvent.INACTIVITY_ELAPSED)

        assert service.snapshot.state is DisplayState.OFF
        assert panel.calls == [("power", False)]


class TestNoPartialFrameOnWake:
    """Invariant 6: leaving OFF shows no partially painted frame — power is set
    before brightness, and both are set together."""

    def test_wake_sets_power_then_brightness(self) -> None:
        service, panel, _, _, _ = _service()
        panel.calls.clear()

        service.handle_event(DisplayEvent.WAKE_REQUEST)

        assert panel.calls == [("power", True), ("brightness", INTERACTIVE_BRIGHTNESS)]


class TestWakeTouchIsConsumed:
    """Invariant 7."""

    def test_a_touch_that_wakes_never_reaches_the_ui(self) -> None:
        service, panel, _, _, _ = _service()
        delivered = []
        service.on_touch(lambda: delivered.append(1))

        panel.simulate_touch()

        assert service.snapshot.state is DisplayState.INTERACTIVE
        assert delivered == []

    def test_a_touch_while_interactive_is_delivered(self) -> None:
        service, panel, _, _, _ = _service()
        service.handle_event(DisplayEvent.WAKE_REQUEST)
        delivered = []
        service.on_touch(lambda: delivered.append(1))

        panel.simulate_touch()

        assert delivered == [1]


class TestNightForcesLedsOff:
    """Invariant 8: night_active forces every user-facing LED to true off, in every
    state where night can coexist with it, and AMBIENT is unreachable while it
    holds."""

    def test_off_with_night_keeps_leds_off(self) -> None:
        service, _, leds, _, _ = _service()
        service.set_night_active(True)
        assert leds.brightness == 0

    def test_interactive_reached_while_night_is_already_active_has_leds_off(self) -> None:
        """Night does not gate WakeRequest (`DISPLAY_STATE_MACHINE.md` has no such
        guard), so INTERACTIVE-while-night is reachable: OFF with night already on,
        then an explicit wake."""
        service, panel, leds, _, _ = _service()
        service.set_night_active(True)

        service.handle_event(DisplayEvent.WAKE_REQUEST)

        assert service.snapshot.state is DisplayState.INTERACTIVE
        assert panel.brightness == NIGHT_MINIMUM
        assert leds.brightness == 0

    def test_setup_stays_reachable_at_night_with_leds_off(self) -> None:
        """Note 13: an administrator mid-configuration is not interrupted."""
        service, panel, leds, _, _ = _service(profile=_profile(role=Role.MANAGER))
        service.handle_event(DisplayEvent.SETUP_REQUESTED)

        service.set_night_active(True)

        assert service.snapshot.state is DisplayState.SETUP
        assert panel.brightness == NIGHT_MINIMUM
        assert leds.brightness == 0

    def test_ambient_cannot_be_entered_while_night_holds(self) -> None:
        service, _, _, _, _ = _service(profile=_profile(role=Role.MANAGER, ambient_enabled=True))
        service.set_night_active(True)

        service.handle_event(DisplayEvent.AMBIENT_REQUESTED)

        assert service.snapshot.state is DisplayState.OFF


class TestDarkRoomIsQuiet:
    """Invariant 3 at the service level: Group B is fully functional in OFF and
    produces no further panel or LED calls. The full scenario (with a real
    `PlaybackSession`) lives in `tests/scenarios/test_dark_room.py`."""

    def test_transport_events_touch_nothing_while_off(self) -> None:
        from aqeno.ports.input import Next, Previous, TogglePlayback, VolumeDelta

        service, panel, leds, _, _ = _service()
        panel.calls.clear()
        leds.calls.clear()

        for event in (VolumeDelta(1), TogglePlayback(), Next(), Previous()):
            service.handle_input(event)

        assert service.snapshot.state is DisplayState.OFF
        assert panel.calls == []
        assert leds.calls == []


class TestGroupDIsInvisibleAtTheService:
    """Invariant 2: playback state changes never touch the panel or LEDs."""

    def test_playback_changes_produce_no_output_calls(self) -> None:
        service, panel, leds, _, _ = _service()
        service.handle_event(DisplayEvent.WAKE_REQUEST)
        panel.calls.clear()
        leds.calls.clear()

        service.handle_playback_changed(_playing())
        service.handle_playback_changed(_stopped())
        service.handle_playback_changed(_playing())

        assert service.snapshot.state is DisplayState.INTERACTIVE
        assert panel.calls == []
        assert leds.calls == []


class TestNothingLeavesOffAutomatically:
    """Invariant 4."""

    def test_off_is_stable_under_timers_transport_and_playback(self) -> None:
        service, panel, _, clock, _ = _service(
            profile=_profile(role=Role.MANAGER, ambient_enabled=True, allows_dim=True)
        )
        panel.calls.clear()

        service.handle_event(DisplayEvent.INACTIVITY_ELAPSED)
        service.handle_event(DisplayEvent.DIM_ELAPSED)
        service.handle_event(DisplayEvent.SETUP_IDLE_ELAPSED)
        service.handle_event(DisplayEvent.AMBIENT_SCHEDULE_END)
        service.handle_playback_changed(_playing())
        clock.advance(timedelta(hours=1))

        assert service.snapshot.state is DisplayState.OFF
        assert panel.calls == []


class TestBrightnessTable:
    """`DISPLAY_STATE_MACHINE.md` § Brightness, reached through real event
    sequences rather than a table drive over an internal seam, so this is exactly
    what a caller of the service would observe."""

    def test_dim_uses_the_profile_dim_level(self) -> None:
        service, panel, _, _, _ = _service(
            profile=_profile(allows_dim=True, dim_hold=timedelta(seconds=15))
        )
        service.handle_event(DisplayEvent.WAKE_REQUEST)

        service.handle_event(DisplayEvent.INACTIVITY_ELAPSED)

        assert service.snapshot.state is DisplayState.DIM
        assert panel.brightness == DIM_BRIGHTNESS

    def test_ambient_uses_the_profile_ambient_level(self) -> None:
        service, panel, _, _, _ = _service(
            profile=_profile(role=Role.MANAGER, ambient_enabled=True)
        )

        service.handle_event(DisplayEvent.AMBIENT_REQUESTED)

        assert service.snapshot.state is DisplayState.AMBIENT
        assert panel.brightness == AMBIENT_BRIGHTNESS

    def test_setup_uses_the_interactive_level(self) -> None:
        service, panel, _, _, _ = _service(profile=_profile(role=Role.MANAGER))

        service.handle_event(DisplayEvent.SETUP_REQUESTED)

        assert service.snapshot.state is DisplayState.SETUP
        assert panel.brightness == INTERACTIVE_BRIGHTNESS


class TestPendingWake:
    """`READINESS_STATES.md` § 4, § 9 invariant 8: one flag, not a queue."""

    def test_wake_before_ui_ready_is_applied_exactly_once_at_ui_ready(self) -> None:
        service, panel, _, _, readiness = _service(ui_ready=False)

        service.handle_event(DisplayEvent.WAKE_REQUEST)
        assert service.snapshot.state is DisplayState.OFF
        assert panel.calls == [("power", False)]  # only the construction-time call

        readiness.advance(ReadinessState.LOCAL_READY)
        readiness.advance(ReadinessState.PLAYBACK_READY)
        readiness.advance(ReadinessState.UI_READY)

        assert service.snapshot.state is DisplayState.INTERACTIVE
        assert panel.calls == [
            ("power", False),
            ("power", True),
            ("brightness", INTERACTIVE_BRIGHTNESS),
        ]

    def test_three_wakes_before_ui_ready_produce_one(self) -> None:
        service, panel, _, _, readiness = _service(ui_ready=False)

        service.handle_event(DisplayEvent.WAKE_REQUEST)
        service.handle_event(DisplayEvent.WAKE_REQUEST)
        service.handle_event(DisplayEvent.WAKE_REQUEST)

        readiness.advance(ReadinessState.LOCAL_READY)
        readiness.advance(ReadinessState.PLAYBACK_READY)
        readiness.advance(ReadinessState.UI_READY)

        assert service.snapshot.state is DisplayState.INTERACTIVE
        power_calls = [call for call in panel.calls if call[0] == "power"]
        assert power_calls == [("power", False), ("power", True)]

    def test_no_pending_wake_means_ui_ready_stays_dark(self) -> None:
        service, panel, _, _, readiness = _service(ui_ready=False)
        panel.calls.clear()

        readiness.advance(ReadinessState.LOCAL_READY)
        readiness.advance(ReadinessState.PLAYBACK_READY)
        readiness.advance(ReadinessState.UI_READY)

        assert service.snapshot.state is DisplayState.OFF
        assert panel.calls == []


class TestDegradedPanel:
    """ADR 0016 § 1: a panel that can only zero the backlight still works, and the
    limitation is surfaced once rather than assumed away."""

    def test_authoritative_off_false_still_drives_power_and_brightness(self) -> None:
        service, panel, _, _, _ = _service(panel=FakeDisplayPanel(authoritative_off=False))
        service.handle_event(DisplayEvent.WAKE_REQUEST)
        assert panel.power_on is True
        assert panel.brightness == INTERACTIVE_BRIGHTNESS

    def test_the_limitation_is_logged_once(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.WARNING, logger="aqeno.application.display"):
            _service(panel=FakeDisplayPanel(authoritative_off=False))
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warnings) == 1


class TestTimers:
    def test_inactivity_timer_uses_the_night_override_when_active(self) -> None:
        """NIGHT_ACTIVATED forces OFF from INTERACTIVE (note 12), so INTERACTIVE
        with `night_active` already true is reached the other way round: night
        turns on while OFF, then an explicit wake — WakeRequest has no guard on
        `night_active`."""
        service, _, _, clock, _ = _service(profile=_profile(night_timeout=timedelta(seconds=10)))
        service.set_night_active(True)

        service.handle_event(DisplayEvent.WAKE_REQUEST)
        assert service.snapshot.state is DisplayState.INTERACTIVE

        clock.advance(timedelta(seconds=9))
        assert service.snapshot.state is DisplayState.INTERACTIVE
        clock.advance(timedelta(seconds=2))
        assert service.snapshot.state is DisplayState.OFF

    def test_setup_idle_timer_shortens_at_night(self) -> None:
        settings = default_settings()
        service, _, _, clock, _ = _service(profile=_profile(role=Role.MANAGER), settings=settings)
        service.handle_event(DisplayEvent.SETUP_REQUESTED)

        service.set_night_active(True)
        clock.advance(timedelta(seconds=settings.display.setup_idle_night - 1))
        assert service.snapshot.state is DisplayState.SETUP
        clock.advance(timedelta(seconds=2))
        assert service.snapshot.state is DisplayState.OFF

    def test_leaving_a_timed_state_cancels_its_timer(self) -> None:
        """The leak `ADR 0016 § Consequences` names: a stale timer must not fire
        into a state it no longer applies to."""
        service, _, _, clock, _ = _service()
        service.handle_event(DisplayEvent.WAKE_REQUEST)
        assert clock.pending == 1

        service.handle_event(DisplayEvent.NIGHT_ACTIVATED)  # forces INTERACTIVE -> OFF
        assert service.snapshot.state is DisplayState.OFF
        assert clock.pending == 0

        clock.advance(timedelta(days=1))
        assert service.snapshot.state is DisplayState.OFF  # no stray INACTIVITY_ELAPSED

    def test_shutdown_cancels_a_pending_timer(self) -> None:
        service, _, _, clock, _ = _service()
        service.handle_event(DisplayEvent.WAKE_REQUEST)
        assert clock.pending == 1

        service.shutdown()

        assert clock.pending == 0


class TestWakeTarget:
    def test_wake_target_follows_playback(self) -> None:
        service, _, _, _, _ = _service()
        assert service.snapshot.wake_target == "home"

        service.handle_playback_changed(_playing())
        assert service.snapshot.wake_target == "now_playing"


class TestListeners:
    def test_on_changed_receives_a_snapshot_on_every_transition(self) -> None:
        service, _, _, _, _ = _service()
        received: list[DisplayState] = []
        service.on_changed(lambda snapshot: received.append(snapshot.state))

        service.handle_event(DisplayEvent.WAKE_REQUEST)

        assert received[-1] is DisplayState.INTERACTIVE
