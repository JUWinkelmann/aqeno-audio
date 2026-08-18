"""Display state machine.

Implements `docs/implementation/DISPLAY_STATE_MACHINE.md` exactly. That document is
normative; where this module and the table disagree, this module is the defect.

The machine is a pure function of (state, event, guards). It owns no timers, touches
no hardware and never decides anything about playback — invariant 1 is that no
transition here can pause, stop or seek audio.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, auto


class DisplayState(StrEnum):
    OFF = "off"
    DIM = "dim"
    INTERACTIVE = "interactive"
    AMBIENT = "ambient"
    SETUP = "setup"


class DisplayEvent(StrEnum):
    # Group A — explicit visual requests
    WAKE_REQUEST = auto()
    TOUCH_ON_PANEL = auto()
    CONTENT_SELECTED = auto()
    AMBIENT_REQUESTED = auto()
    AMBIENT_EXITED = auto()
    SETUP_REQUESTED = auto()
    SETUP_COMPLETED = auto()

    # Group B — physical transport
    VOLUME_DELTA = auto()
    TOGGLE_PLAYBACK = auto()
    NEXT = auto()
    PREVIOUS = auto()

    # Group C — NFC
    NFC_PRESENTED = auto()
    NFC_REMOVED = auto()

    # Group D — playback and system
    PLAYBACK_STARTED = auto()
    PLAYBACK_STOPPED = auto()
    PLAYBACK_PAUSED = auto()
    TRACK_CHANGED = auto()
    BUFFERING_STARTED = auto()
    BUFFERING_ENDED = auto()
    METADATA_UPDATED = auto()
    PLAYBACK_ERROR = auto()
    NETWORK_CHANGED = auto()
    SERVICE_READY = auto()
    VOLUME_CHANGED = auto()

    # Group E — timers
    INACTIVITY_ELAPSED = auto()
    DIM_ELAPSED = auto()
    SETUP_IDLE_ELAPSED = auto()
    AMBIENT_SCHEDULE_START = auto()
    AMBIENT_SCHEDULE_END = auto()

    # Group F — policy
    NIGHT_ACTIVATED = auto()
    NIGHT_DEACTIVATED = auto()


TRANSPORT_EVENTS = frozenset(
    {
        DisplayEvent.VOLUME_DELTA,
        DisplayEvent.TOGGLE_PLAYBACK,
        DisplayEvent.NEXT,
        DisplayEvent.PREVIOUS,
    }
)
"""Group B. Never changes display state, never resets the visual inactivity timer."""

NFC_EVENTS = frozenset({DisplayEvent.NFC_PRESENTED, DisplayEvent.NFC_REMOVED})
"""Group C. Presenting a token is a physical action; it does not wake the display."""

PLAYBACK_AND_SYSTEM_EVENTS = frozenset(
    {
        DisplayEvent.PLAYBACK_STARTED,
        DisplayEvent.PLAYBACK_STOPPED,
        DisplayEvent.PLAYBACK_PAUSED,
        DisplayEvent.TRACK_CHANGED,
        DisplayEvent.BUFFERING_STARTED,
        DisplayEvent.BUFFERING_ENDED,
        DisplayEvent.METADATA_UPDATED,
        DisplayEvent.PLAYBACK_ERROR,
        DisplayEvent.NETWORK_CHANGED,
        DisplayEvent.SERVICE_READY,
        DisplayEvent.VOLUME_CHANGED,
    }
)
"""Group D. Invisible: produces no transition in any state, ever."""


@dataclass(frozen=True, slots=True)
class DisplayGuards:
    """Read at transition time, never cached. See the guard table in the spec."""

    ui_ready: bool = False
    night_active: bool = False
    playback_active: bool = False
    ambient_enabled: bool = False
    ambient_authorised: bool = False
    profile_allows_dim: bool = False
    setup_authorised: bool = False

    def ambient_permitted(self) -> bool:
        """Note 4. Ambient is never an automatic fallback for inactivity."""
        return (
            self.ambient_enabled
            and self.ambient_authorised
            and not self.night_active
            and not self.playback_active
        )


@dataclass(frozen=True, slots=True)
class DisplayTransition:
    state: DisplayState
    reset_inactivity_timer: bool = False
    consume_touch: bool = False
    """Note 2: the touch that wakes the panel must not reach the control beneath it."""
    defer_until_ready: bool = False
    """Note 1: a wake before UI_READY is queued by the caller, never discarded."""
    blocked_reason: str | None = None
    """Why a requested transition did not happen. For logging, not for the UI."""


def _stay(state: DisplayState, *, reason: str | None = None) -> DisplayTransition:
    return DisplayTransition(state=state, blocked_reason=reason)


def _reset(state: DisplayState) -> DisplayTransition:
    return DisplayTransition(state=state, reset_inactivity_timer=True)


def _wake(current: DisplayState, guards: DisplayGuards, *, by_touch: bool) -> DisplayTransition:
    """Enter INTERACTIVE from OFF, DIM or AMBIENT."""
    if not guards.ui_ready:
        return DisplayTransition(state=current, defer_until_ready=True)
    return DisplayTransition(
        state=DisplayState.INTERACTIVE,
        reset_inactivity_timer=True,
        consume_touch=by_touch,
    )


def _enter_ambient(current: DisplayState, guards: DisplayGuards) -> DisplayTransition:
    if not guards.ui_ready:
        return _stay(current, reason="ui_not_ready")
    if not guards.ambient_permitted():
        return _stay(current, reason="ambient_not_permitted")
    return DisplayTransition(state=DisplayState.AMBIENT)


def resolve(current: DisplayState, event: DisplayEvent, guards: DisplayGuards) -> DisplayTransition:
    """Resolve one cell of the transition table.

    Total: every (state, event) pair has exactly one defined outcome (invariant 10).
    """
    # Invariants 2 and 3: transport and system events are invisible in every state,
    # and do not extend the time the screen stays on. The timer measures *visual*
    # interaction — this is the dark-room requirement in its most literal form.
    if event in TRANSPORT_EVENTS or event in PLAYBACK_AND_SYSTEM_EVENTS:
        return _stay(current)

    # Note 7 and 8: NFC never wakes the display; in SETUP it feeds tag assignment.
    if event in NFC_EVENTS:
        return _reset(current) if current is DisplayState.SETUP else _stay(current)

    match event:
        case DisplayEvent.WAKE_REQUEST:
            if current in (DisplayState.OFF, DisplayState.DIM, DisplayState.AMBIENT):
                return _wake(current, guards, by_touch=False)
            return _reset(current)

        case DisplayEvent.TOUCH_ON_PANEL:
            if current in (DisplayState.OFF, DisplayState.DIM, DisplayState.AMBIENT):
                return _wake(current, guards, by_touch=True)
            return _reset(current)

        case DisplayEvent.CONTENT_SELECTED:
            if current in (DisplayState.INTERACTIVE, DisplayState.SETUP):
                return _reset(current)
            return _stay(current)

        case DisplayEvent.AMBIENT_REQUESTED:
            if current in (DisplayState.OFF, DisplayState.DIM, DisplayState.INTERACTIVE):
                return _enter_ambient(current, guards)
            return _stay(current)

        case DisplayEvent.AMBIENT_EXITED:
            if current is DisplayState.AMBIENT:
                return _reset(DisplayState.INTERACTIVE)
            return _stay(current)

        case DisplayEvent.SETUP_REQUESTED:
            if current is DisplayState.SETUP:
                return _reset(current)
            if not guards.ui_ready:
                # A lit panel with nothing rendered on it is worse than a request
                # that did not happen. Setup is adult-initiated and can be retried.
                return _stay(current, reason="ui_not_ready")
            if not guards.setup_authorised:
                return _stay(current, reason="setup_not_authorised")
            return _reset(DisplayState.SETUP)

        case DisplayEvent.SETUP_COMPLETED:
            if current is DisplayState.SETUP:
                return _reset(DisplayState.INTERACTIVE)
            return _stay(current)

        case DisplayEvent.INACTIVITY_ELAPSED:
            if current is DisplayState.DIM:
                return _stay(DisplayState.OFF)
            if current is DisplayState.INTERACTIVE:
                # Glanceable DIM is playback context, never an automatic idle
                # surface. Night/Bedtime keeps authority and goes fully dark.
                if guards.profile_allows_dim and guards.playback_active and not guards.night_active:
                    return _stay(DisplayState.DIM)
                return _stay(DisplayState.OFF)
            # Note 9: inactivity does not apply in AMBIENT. OFF and SETUP: n/a.
            return _stay(current)

        case DisplayEvent.DIM_ELAPSED:
            if current is DisplayState.DIM:
                return _stay(DisplayState.OFF)
            return _stay(current)

        case DisplayEvent.SETUP_IDLE_ELAPSED:
            # Note 10: a forgotten configuration screen must not light a bedroom.
            if current is DisplayState.SETUP:
                return _stay(DisplayState.OFF)
            return _stay(current)

        case DisplayEvent.AMBIENT_SCHEDULE_START:
            # Note 11: Ambient waits rather than interrupting an active user.
            if current in (DisplayState.OFF, DisplayState.DIM):
                return _enter_ambient(current, guards)
            return _stay(current)

        case DisplayEvent.AMBIENT_SCHEDULE_END:
            if current is DisplayState.AMBIENT:
                return _stay(DisplayState.OFF)
            return _stay(current)

        case DisplayEvent.NIGHT_ACTIVATED:
            # Note 13: an administrator mid-configuration is not interrupted.
            if current is DisplayState.SETUP:
                return _stay(current)
            return _stay(DisplayState.OFF)

        case DisplayEvent.NIGHT_DEACTIVATED:
            # Note 14 and invariant 4: nothing ever leaves OFF automatically.
            return _stay(current)

    raise AssertionError(f"unhandled display event: {event}")  # pragma: no cover


def wake_target(guards: DisplayGuards) -> str:
    """Which view a wake into INTERACTIVE lands on.

    During playback the relevant view is what is playing, not a grid of alternatives
    inviting a new choice. See the spec's § Wake target; confirm in user testing.
    """
    return "now_playing" if guards.playback_active else "home"
