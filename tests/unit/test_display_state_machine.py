"""Table-driven tests for the display state machine.

The specification is a table, so the test is a table. A missing cell is a failure,
not an oversight (ADR 0008 § 5). The ten invariants each get a named test below.
"""

from __future__ import annotations

import pytest

from aqeno.domain.display import (
    NFC_EVENTS,
    PLAYBACK_AND_SYSTEM_EVENTS,
    TRANSPORT_EVENTS,
    DisplayEvent,
    DisplayGuards,
    DisplayState,
    resolve,
    wake_target,
)

ALL_STATES = list(DisplayState)
ALL_EVENTS = list(DisplayEvent)

READY = DisplayGuards(ui_ready=True)
READY_WITH_PLAYBACK_DIM = DisplayGuards(
    ui_ready=True, playback_active=True, profile_allows_dim=True
)
READY_FOR_SETUP = DisplayGuards(ui_ready=True, setup_authorised=True)
READY_FOR_AMBIENT = DisplayGuards(ui_ready=True, ambient_enabled=True, ambient_authorised=True)


class TestTotality:
    """Invariant 10: exactly one defined outcome for every state/event pair."""

    @pytest.mark.parametrize("state", ALL_STATES)
    @pytest.mark.parametrize("event", ALL_EVENTS)
    def test_every_cell_resolves(self, state: DisplayState, event: DisplayEvent) -> None:
        transition = resolve(state, event, READY)
        assert isinstance(transition.state, DisplayState)

    @pytest.mark.parametrize("state", ALL_STATES)
    @pytest.mark.parametrize("event", ALL_EVENTS)
    def test_resolution_is_deterministic(self, state: DisplayState, event: DisplayEvent) -> None:
        assert resolve(state, event, READY) == resolve(state, event, READY)


class TestExplicitWake:
    @pytest.mark.parametrize("start", [DisplayState.OFF, DisplayState.DIM, DisplayState.AMBIENT])
    @pytest.mark.parametrize("event", [DisplayEvent.WAKE_REQUEST, DisplayEvent.TOUCH_ON_PANEL])
    def test_explicit_request_enters_interactive(
        self, start: DisplayState, event: DisplayEvent
    ) -> None:
        transition = resolve(start, event, READY)
        assert transition.state is DisplayState.INTERACTIVE
        assert transition.reset_inactivity_timer

    def test_wake_touch_is_consumed(self) -> None:
        """Invariant 7. A child tapping a dark panel must not trigger the control
        beneath their finger, which they cannot see."""
        transition = resolve(DisplayState.OFF, DisplayEvent.TOUCH_ON_PANEL, READY)
        assert transition.consume_wake_input is True

    def test_touch_while_interactive_reaches_the_ui(self) -> None:
        transition = resolve(DisplayState.INTERACTIVE, DisplayEvent.TOUCH_ON_PANEL, READY)
        assert transition.consume_wake_input is False
        assert transition.reset_inactivity_timer

    def test_wake_before_ui_ready_is_deferred_not_discarded(self) -> None:
        transition = resolve(
            DisplayState.OFF, DisplayEvent.WAKE_REQUEST, DisplayGuards(ui_ready=False)
        )
        assert transition.state is DisplayState.OFF
        assert transition.defer_until_ready is True

    def test_wake_target_follows_playback(self) -> None:
        assert wake_target(DisplayGuards(playback_active=True)) == "now_playing"
        assert wake_target(DisplayGuards(playback_active=False)) == "home"


class TestTransportEventsAreInvisible:
    """Invariant 3, and the dark-room requirement in its most literal form."""

    @pytest.mark.parametrize("state", ALL_STATES)
    @pytest.mark.parametrize("event", sorted(TRANSPORT_EVENTS))
    def test_transport_never_changes_state(self, state: DisplayState, event: DisplayEvent) -> None:
        assert resolve(state, event, READY).state is state

    @pytest.mark.parametrize("state", ALL_STATES)
    @pytest.mark.parametrize("event", sorted(TRANSPORT_EVENTS))
    def test_transport_never_extends_screen_time(
        self, state: DisplayState, event: DisplayEvent
    ) -> None:
        """The timer measures visual interaction. Turning the volume down at 3 a.m.
        is not a request to keep the screen on."""
        assert resolve(state, event, READY).reset_inactivity_timer is False

    def test_volume_works_in_the_dark_without_waking(self) -> None:
        night = DisplayGuards(ui_ready=True, night_active=True, playback_active=True)
        transition = resolve(DisplayState.OFF, DisplayEvent.VOLUME_DELTA, night)
        assert transition.state is DisplayState.OFF
        assert transition.consume_wake_input is False


class TestGroupGNavigation:
    """Group G, notes 15-16. Navigation replaces the touch AQENO must not require,
    so it wakes like a touch — and never like transport."""

    @pytest.mark.parametrize("start", [DisplayState.OFF, DisplayState.DIM, DisplayState.AMBIENT])
    def test_navigation_wakes_and_is_consumed(self, start: DisplayState) -> None:
        transition = resolve(start, DisplayEvent.NAVIGATE, READY)
        assert transition.state is DisplayState.INTERACTIVE
        assert transition.consume_wake_input is True

    def test_navigation_while_interactive_reaches_the_ui(self) -> None:
        transition = resolve(DisplayState.INTERACTIVE, DisplayEvent.NAVIGATE, READY)
        assert transition.state is DisplayState.INTERACTIVE
        assert transition.consume_wake_input is False
        assert transition.reset_inactivity_timer

    def test_navigation_before_ui_ready_is_deferred(self) -> None:
        transition = resolve(DisplayState.OFF, DisplayEvent.NAVIGATE, DisplayGuards(ui_ready=False))
        assert transition.state is DisplayState.OFF
        assert transition.defer_until_ready is True

    def test_navigation_is_not_a_transport_event(self) -> None:
        """If NAVIGATE ever joins Group B, the dark room stays dark and the device
        becomes unusable without touch. Both properties are load-bearing."""
        assert DisplayEvent.NAVIGATE not in TRANSPORT_EVENTS


class TestGroupDIsInvisible:
    """Invariant 2. Buffering, chapter changes and metadata never wake anything."""

    @pytest.mark.parametrize("state", ALL_STATES)
    @pytest.mark.parametrize("event", sorted(PLAYBACK_AND_SYSTEM_EVENTS))
    def test_group_d_events_produce_no_transition(
        self, state: DisplayState, event: DisplayEvent
    ) -> None:
        transition = resolve(state, event, READY)
        assert transition.state is state
        assert transition.reset_inactivity_timer is False


class TestNfc:
    @pytest.mark.parametrize("state", [DisplayState.OFF, DisplayState.DIM, DisplayState.AMBIENT])
    @pytest.mark.parametrize("event", sorted(NFC_EVENTS))
    def test_nfc_does_not_wake_the_display(self, state: DisplayState, event: DisplayEvent) -> None:
        """Note 7. A figure placed on the device at bedtime must not light the room."""
        assert resolve(state, event, READY).state is state

    @pytest.mark.parametrize("event", sorted(NFC_EVENTS))
    def test_nfc_in_setup_feeds_tag_assignment(self, event: DisplayEvent) -> None:
        transition = resolve(DisplayState.SETUP, event, READY)
        assert transition.state is DisplayState.SETUP
        assert transition.reset_inactivity_timer is True


class TestInactivity:
    def test_idle_profile_goes_straight_to_off(self) -> None:
        transition = resolve(DisplayState.INTERACTIVE, DisplayEvent.INACTIVITY_ELAPSED, READY)
        assert transition.state is DisplayState.OFF

    def test_dim_is_used_only_during_playback_where_the_profile_allows_it(self) -> None:
        transition = resolve(
            DisplayState.INTERACTIVE,
            DisplayEvent.INACTIVITY_ELAPSED,
            READY_WITH_PLAYBACK_DIM,
        )
        assert transition.state is DisplayState.DIM

    def test_night_skips_dim_even_during_playback(self) -> None:
        guards = DisplayGuards(
            ui_ready=True,
            playback_active=True,
            profile_allows_dim=True,
            night_active=True,
        )
        transition = resolve(DisplayState.INTERACTIVE, DisplayEvent.INACTIVITY_ELAPSED, guards)
        assert transition.state is DisplayState.OFF

    def test_dim_elapses_to_off(self) -> None:
        assert resolve(DisplayState.DIM, DisplayEvent.DIM_ELAPSED, READY).state is DisplayState.OFF

    def test_inactivity_does_not_apply_in_ambient(self) -> None:
        transition = resolve(
            DisplayState.AMBIENT, DisplayEvent.INACTIVITY_ELAPSED, READY_FOR_AMBIENT
        )
        assert transition.state is DisplayState.AMBIENT

    def test_forgotten_setup_screen_goes_dark(self) -> None:
        transition = resolve(DisplayState.SETUP, DisplayEvent.SETUP_IDLE_ELAPSED, READY)
        assert transition.state is DisplayState.OFF


class TestAmbientIsNeverAutomatic:
    @pytest.mark.parametrize(
        "guards",
        [
            DisplayGuards(ui_ready=True),
            DisplayGuards(ui_ready=True, ambient_enabled=True),
            DisplayGuards(ui_ready=True, ambient_authorised=True),
        ],
        ids=["nothing_enabled", "enabled_unauthorised", "authorised_disabled"],
    )
    def test_ambient_requires_enabled_and_authorised(self, guards: DisplayGuards) -> None:
        transition = resolve(DisplayState.OFF, DisplayEvent.AMBIENT_REQUESTED, guards)
        assert transition.state is DisplayState.OFF
        assert transition.blocked_reason == "ambient_not_permitted"

    def test_ambient_is_refused_before_the_ui_can_render_it(self) -> None:
        """Entering AMBIENT before UI_READY would light a panel with nothing on it."""
        guards = DisplayGuards(ui_ready=False, ambient_enabled=True, ambient_authorised=True)
        for event in (DisplayEvent.AMBIENT_REQUESTED, DisplayEvent.AMBIENT_SCHEDULE_START):
            transition = resolve(DisplayState.OFF, event, guards)
            assert transition.state is DisplayState.OFF
            assert transition.blocked_reason == "ui_not_ready"

    def test_ambient_is_refused_during_playback(self) -> None:
        """Not visual accompaniment to an audio story."""
        guards = DisplayGuards(
            ui_ready=True,
            ambient_enabled=True,
            ambient_authorised=True,
            playback_active=True,
        )
        assert (
            resolve(DisplayState.OFF, DisplayEvent.AMBIENT_REQUESTED, guards).state
            is DisplayState.OFF
        )

    def test_ambient_is_refused_at_night(self) -> None:
        guards = DisplayGuards(
            ui_ready=True,
            ambient_enabled=True,
            ambient_authorised=True,
            night_active=True,
        )
        assert (
            resolve(DisplayState.OFF, DisplayEvent.AMBIENT_SCHEDULE_START, guards).state
            is DisplayState.OFF
        )

    def test_schedule_waits_rather_than_interrupting(self) -> None:
        """Note 11."""
        transition = resolve(
            DisplayState.INTERACTIVE,
            DisplayEvent.AMBIENT_SCHEDULE_START,
            READY_FOR_AMBIENT,
        )
        assert transition.state is DisplayState.INTERACTIVE

    def test_schedule_start_from_off_enters_ambient(self) -> None:
        transition = resolve(
            DisplayState.OFF, DisplayEvent.AMBIENT_SCHEDULE_START, READY_FOR_AMBIENT
        )
        assert transition.state is DisplayState.AMBIENT


class TestSetupAuthorisation:
    def test_setup_requires_authorisation(self) -> None:
        transition = resolve(DisplayState.OFF, DisplayEvent.SETUP_REQUESTED, READY)
        assert transition.state is DisplayState.OFF
        assert transition.blocked_reason == "setup_not_authorised"

    def test_setup_is_refused_before_the_ui_can_render_it(self) -> None:
        """Adult-initiated and retryable, so blocking beats a lit blank panel."""
        guards = DisplayGuards(ui_ready=False, setup_authorised=True)
        transition = resolve(DisplayState.OFF, DisplayEvent.SETUP_REQUESTED, guards)
        assert transition.state is DisplayState.OFF
        assert transition.blocked_reason == "ui_not_ready"

    @pytest.mark.parametrize(
        "start", [DisplayState.OFF, DisplayState.DIM, DisplayState.INTERACTIVE]
    )
    def test_authorised_setup_is_reachable(self, start: DisplayState) -> None:
        assert (
            resolve(start, DisplayEvent.SETUP_REQUESTED, READY_FOR_SETUP).state
            is DisplayState.SETUP
        )

    def test_setup_completes_into_interactive(self) -> None:
        assert (
            resolve(DisplayState.SETUP, DisplayEvent.SETUP_COMPLETED, READY).state
            is DisplayState.INTERACTIVE
        )


class TestNightPolicy:
    @pytest.mark.parametrize(
        "start",
        [DisplayState.OFF, DisplayState.DIM, DisplayState.INTERACTIVE, DisplayState.AMBIENT],
    )
    def test_night_forces_off(self, start: DisplayState) -> None:
        assert resolve(start, DisplayEvent.NIGHT_ACTIVATED, READY).state is DisplayState.OFF

    def test_night_does_not_interrupt_setup(self) -> None:
        """Note 13: an administrator mid-configuration keeps their screen."""
        assert (
            resolve(DisplayState.SETUP, DisplayEvent.NIGHT_ACTIVATED, READY).state
            is DisplayState.SETUP
        )

    @pytest.mark.parametrize("state", ALL_STATES)
    def test_night_ending_never_wakes_anything(self, state: DisplayState) -> None:
        """Invariant 4, note 14."""
        assert resolve(state, DisplayEvent.NIGHT_DEACTIVATED, READY).state is state


EXPLICIT_WAKE_EVENTS = frozenset(
    {
        DisplayEvent.WAKE_REQUEST,
        DisplayEvent.TOUCH_ON_PANEL,
        # Group G is a human hand on a physical control, so invariant 4 holds:
        # nothing here leaves OFF without a person asking for it.
        DisplayEvent.NAVIGATE,
        DisplayEvent.SETUP_REQUESTED,
        DisplayEvent.AMBIENT_REQUESTED,
        DisplayEvent.AMBIENT_SCHEDULE_START,
    }
)

AUTOMATIC_EVENTS = [event for event in ALL_EVENTS if event not in EXPLICIT_WAKE_EVENTS]


class TestNothingLeavesOffAutomatically:
    """Invariant 4. The only paths out of OFF are an explicit human request or an
    authorised Ambient schedule."""

    @pytest.mark.parametrize("event", AUTOMATIC_EVENTS)
    def test_off_is_stable_under_every_automatic_event(self, event: DisplayEvent) -> None:
        guards = DisplayGuards(
            ui_ready=True,
            playback_active=True,
            ambient_enabled=True,
            ambient_authorised=True,
            profile_allows_dim=True,
            setup_authorised=True,
        )
        assert resolve(DisplayState.OFF, event, guards).state is DisplayState.OFF
