"""The display service — drives `domain/display.py`, ADR 0016.

Owns the current `DisplayState`, the three visual timers, and everything that
decides panel power, panel brightness and LED brightness. Nothing outside this
module and `adapters/` may touch a `DisplayPanel` or `StatusLeds` (`AGENTS.md`
Architecture rules; `PLATFORM_CONTRACTS.md` § Display contract as amended by
ADR 0016).

Guards are assembled fresh at every transition (`domain/display.py`'s own
docstring: "All are read at transition time, never cached") from state this
service owns — `night_active`, `playback_active` — and from the profile and
readiness ladder it was constructed with.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

from aqeno.application.playback import PlaybackSnapshot
from aqeno.application.readiness import Readiness, ReadinessState
from aqeno.config.defaults import Settings
from aqeno.domain.display import (
    DisplayEvent,
    DisplayGuards,
    DisplayState,
    DisplayTransition,
    resolve,
    wake_target,
)
from aqeno.domain.profile import Profile
from aqeno.ports.ambient_light import AmbientLight
from aqeno.ports.audio import TransportState
from aqeno.ports.clock import Clock
from aqeno.ports.display import DisplayPanel
from aqeno.ports.input import (
    InputEvent,
    Next,
    NfcPresented,
    NfcRemoved,
    Previous,
    TogglePlayback,
    VolumeDelta,
    WakeRequest,
)
from aqeno.ports.led import StatusLeds

logger = logging.getLogger(__name__)

_AMBIENT_LIGHT_ALPHA = 0.25
_DARK_LUX_ENTER = 10.0
_DARK_LUX_EXIT = 15.0

_INPUT_EVENT_MAP: dict[type, DisplayEvent] = {
    VolumeDelta: DisplayEvent.VOLUME_DELTA,
    TogglePlayback: DisplayEvent.TOGGLE_PLAYBACK,
    Next: DisplayEvent.NEXT,
    Previous: DisplayEvent.PREVIOUS,
    WakeRequest: DisplayEvent.WAKE_REQUEST,
    NfcPresented: DisplayEvent.NFC_PRESENTED,
    NfcRemoved: DisplayEvent.NFC_REMOVED,
}
"""Every `InputBus` event this service can receive, mapped onto its display event.
Group B and NFC map straight through: the domain machine already guarantees they
never change state or reset a timer, so no special-casing is needed here to keep
the dark room dark — routing them through `resolve()` uniformly is what makes that
guarantee mechanical rather than trusted."""

_NIGHT_EVENTS = frozenset({DisplayEvent.NIGHT_ACTIVATED, DisplayEvent.NIGHT_DEACTIVATED})
"""Night can change the applicable timeout and brightness for a state the machine
itself reports as unchanged (SETUP, notes 12-13) — a policy concern the domain's
`reset_inactivity_timer` flag does not speak to. The service always re-derives
output and re-schedules the timer for these two events, regardless of that flag."""


@dataclass(frozen=True, slots=True)
class DisplaySnapshot:
    """Application-owned state exposed to presentation, in the shape of
    `PlaybackSnapshot`: a frozen value plus a listener, never a live object."""

    state: DisplayState
    wake_target: str
    """Which view a wake into INTERACTIVE would land on right now — see the
    domain's § Wake target. Meaningful only while not already INTERACTIVE."""


DisplayListener = Callable[[DisplaySnapshot], None]
UiTouchListener = Callable[[], None]


class DisplayService:
    """Coordinates one panel and one LED strip under the display policy."""

    def __init__(
        self,
        *,
        panel: DisplayPanel,
        leds: StatusLeds,
        clock: Clock,
        readiness: Readiness,
        profile: Profile,
        settings: Settings,
        ambient_light: AmbientLight | None = None,
    ) -> None:
        self._panel = panel
        self._leds = leds
        self._clock = clock
        self._readiness = readiness
        self._profile = profile
        self._settings = settings
        self._ambient_light = ambient_light
        self._lock = threading.RLock()

        self._state = DisplayState.OFF
        self._night_active = False
        self._playback_active = False
        self._pending_wake = False
        self._timer_handle: object | None = None
        self._listeners: list[DisplayListener] = []
        self._ui_touch_listener: UiTouchListener | None = None
        self._smoothed_lux: float | None = None
        self._ambient_dark = False
        self._illumination_preference = settings.controls.illumination

        # Sentinels, not real values: force the first `_apply_outputs()` to make
        # its calls explicitly rather than assuming the adapter already agrees
        # with OFF/true-off (invariant 9 holds from process start, not by luck).
        self._last_power: bool | None = None
        self._last_brightness: int | None = None
        self._last_led: int | None = None
        self._panel_failed = False
        self._leds_failed = False

        try:
            capabilities = panel.capabilities()
            if not capabilities.authoritative_off:
                logger.warning(
                    "display panel cannot guarantee authoritative OFF; a zero backlight "
                    "is not a true dark panel (ADR 0016 § 1, gap G24)"
                )
        except Exception:
            logger.exception("display panel unavailable; continuing headless")
            self._panel_failed = True

        self._apply_outputs(self._guards())
        readiness.on_reached(ReadinessState.UI_READY, self._apply_pending_wake)
        if not self._panel_failed:
            try:
                panel.on_touch(self.handle_touch)
            except Exception:
                logger.exception("display touch unavailable; continuing without touch")

    # -- presentation ------------------------------------------------------

    @property
    def snapshot(self) -> DisplaySnapshot:
        with self._lock:
            return self._snapshot()

    def on_changed(self, listener: DisplayListener) -> None:
        with self._lock:
            self._listeners.append(listener)

    def on_touch(self, listener: UiTouchListener) -> None:
        """Register the UI's touch handler. Never called for a touch that woke the
        panel (ADR 0016 § 3, invariant 7) — the service decides that, not the UI."""
        with self._lock:
            self._ui_touch_listener = listener

    # -- input ---------------------------------------------------------------

    def handle_input(self, event: InputEvent) -> None:
        """Subscribed to the `InputBus`, alongside `PlaybackSession.handle_input`."""
        display_event = _INPUT_EVENT_MAP.get(type(event))
        if display_event is not None:
            self.handle_event(display_event)

    def handle_touch(self) -> None:
        """Registered as the panel's touch listener. Swallows a wake touch; forwards
        any other touch to the UI listener, if one is registered."""
        with self._lock:
            transition = self.handle_event(DisplayEvent.TOUCH_ON_PANEL)
            if not transition.consume_touch and self._ui_touch_listener is not None:
                self._ui_touch_listener()

    def handle_playback_changed(self, snapshot: PlaybackSnapshot) -> None:
        """Subscribed to `PlaybackSession.on_changed`. Only `playback_active` (the
        `DisplayGuards` guard, not the display state itself) is derived from it —
        Group D events stay invisible to the display machine (invariant 2); this is
        what makes them so."""
        active = snapshot.transport in (TransportState.PLAYING, TransportState.PAUSED)
        with self._lock:
            if active == self._playback_active:
                return
            self._playback_active = active
            self._notify_changed()

    def shutdown(self) -> None:
        """Cancel any pending visual timer. A stale timer callback firing into a
        service the process is tearing down is the leak ADR 0016 § Consequences
        names explicitly."""
        with self._lock:
            self._cancel_timer()

    def set_night_active(self, active: bool) -> None:
        """Mirrors `PlaybackSession.set_night_active`. The composition root calls
        both — see ADR 0016 § Out of scope on why that duplication stands."""
        with self._lock:
            if active == self._night_active:
                return
            self._night_active = active
            self.handle_event(
                DisplayEvent.NIGHT_ACTIVATED if active else DisplayEvent.NIGHT_DEACTIVATED
            )

    def set_illumination_preference(self, preference: str) -> None:
        if preference not in {"off", "subtle", "clear"}:
            raise ValueError("unsupported illumination preference")
        with self._lock:
            self._illumination_preference = preference
            self._apply_outputs(self._guards())

    def sample_ambient_light(self) -> None:
        """Apply one calm sensor sample to display output.

        RH1 owns when samples are requested. The service only performs the
        minimum interpretation required to prevent a DIM panel oscillating near
        a threshold: an exponential smoothing step and a 10/15 lux hysteresis.
        """
        if self._ambient_light is None:
            return
        lux = max(0.0, self._ambient_light.read_lux())
        with self._lock:
            if self._smoothed_lux is None:
                self._smoothed_lux = lux
            else:
                self._smoothed_lux += _AMBIENT_LIGHT_ALPHA * (lux - self._smoothed_lux)

            previous = self._ambient_dark
            if self._ambient_dark:
                self._ambient_dark = self._smoothed_lux < _DARK_LUX_EXIT
            else:
                self._ambient_dark = self._smoothed_lux <= _DARK_LUX_ENTER
            if self._ambient_dark != previous:
                self._apply_outputs(self._guards())

    # -- the machine -----------------------------------------------------------

    def handle_event(self, event: DisplayEvent) -> DisplayTransition:
        """Resolve one event against the domain machine and apply its effects.

        The single entry point every event above funnels through, and also the one
        a table-driven test suite drives directly to exercise every (state, event,
        guard) cell at the service layer, where timers and output actually live.
        """
        with self._lock:
            previous_state = self._state
            guards = self._guards()
            transition = resolve(previous_state, event, guards)

            if transition.defer_until_ready:
                self._pending_wake = True

            self._state = transition.state
            state_changed = transition.state != previous_state
            if transition.reset_inactivity_timer or state_changed or event in _NIGHT_EVENTS:
                self._reschedule(guards)

            self._apply_outputs(guards)
            self._notify_changed()
            return transition

    def _apply_pending_wake(self) -> None:
        with self._lock:
            if self._pending_wake:
                self._pending_wake = False
                self.handle_event(DisplayEvent.WAKE_REQUEST)

    def _guards(self) -> DisplayGuards:
        return DisplayGuards(
            ui_ready=self._readiness.has_reached(ReadinessState.UI_READY),
            night_active=self._night_active,
            playback_active=self._playback_active,
            ambient_enabled=self._profile.ambient_enabled,
            ambient_authorised=self._profile.role.may_manage(),
            profile_allows_dim=self._profile.display.allows_dim,
            setup_authorised=self._profile.role.may_manage(),
        )

    def _snapshot(self) -> DisplaySnapshot:
        return DisplaySnapshot(state=self._state, wake_target=wake_target(self._guards()))

    def _notify_changed(self) -> None:
        snapshot = self._snapshot()
        for listener in tuple(self._listeners):
            listener(snapshot)

    # -- timers --------------------------------------------------------------

    def _reschedule(self, guards: DisplayGuards) -> None:
        self._cancel_timer()
        policy = self._profile.display
        if self._state is DisplayState.DIM:
            if policy.dim_hold is not None:
                self._timer_handle = self._clock.schedule(
                    policy.dim_hold, self._fire(DisplayEvent.DIM_ELAPSED)
                )
        elif self._state is DisplayState.INTERACTIVE:
            timeout = policy.night_timeout if guards.night_active else policy.inactivity_timeout
            self._timer_handle = self._clock.schedule(
                timeout, self._fire(DisplayEvent.INACTIVITY_ELAPSED)
            )
        elif self._state is DisplayState.SETUP:
            seconds = (
                self._settings.display.setup_idle_night
                if guards.night_active
                else self._settings.display.setup_idle
            )
            self._timer_handle = self._clock.schedule(
                timedelta(seconds=seconds), self._fire(DisplayEvent.SETUP_IDLE_ELAPSED)
            )
        # OFF and AMBIENT own no internal timer: OFF has nothing to time out of on
        # its own (invariant 4), and AMBIENT's schedule is driven from outside.

    def _fire(self, event: DisplayEvent) -> Callable[[], None]:
        def _callback() -> None:
            self.handle_event(event)

        return _callback

    def _cancel_timer(self) -> None:
        if self._timer_handle is not None:
            self._clock.cancel(self._timer_handle)
            self._timer_handle = None

    # -- output ----------------------------------------------------------------

    def _apply_outputs(self, guards: DisplayGuards) -> None:
        power, brightness = self._power_and_brightness(guards)
        led_brightness = self._led_brightness(guards)

        if not self._panel_failed:
            try:
                if power != self._last_power:
                    self._panel.set_power(power)
                    self._last_power = power
                    if not power:
                        # Brightness is meaningless while off; force it to be re-applied
                        # explicitly the next time the panel powers on rather than relying
                        # on the adapter to remember (invariant 5: no flash on entering OFF,
                        # invariant 6: no partially painted frame on leaving it).
                        self._last_brightness = None

                if power and brightness != self._last_brightness:
                    self._panel.set_brightness(brightness)
                    self._last_brightness = brightness
            except Exception:
                logger.exception("display panel failed; continuing headless")
                self._panel_failed = True

        if not self._leds_failed and led_brightness != self._last_led:
            try:
                self._leds.set_brightness(led_brightness)
                self._last_led = led_brightness
            except Exception:
                logger.exception("status LEDs failed; continuing without illumination")
                self._leds_failed = True

    def _power_and_brightness(self, guards: DisplayGuards) -> tuple[bool, int]:
        """`DISPLAY_STATE_MACHINE.md` § Brightness, read from the profile's already
        config-resolved `DisplayPolicy` — never a literal value here."""
        policy = self._profile.display

        def night_or(normal: int) -> int:
            return policy.night_brightness if guards.night_active else normal

        match self._state:
            case DisplayState.OFF:
                return False, 0
            case DisplayState.DIM:
                brightness = policy.dim_brightness
                if self._ambient_dark:
                    brightness = max(1, brightness // 2)
                return True, night_or(brightness)
            case DisplayState.AMBIENT:
                # Unreachable while night_active (invariant 8); no night column to read.
                return True, policy.ambient_brightness
            case DisplayState.INTERACTIVE | DisplayState.SETUP:
                return True, night_or(policy.interactive_brightness)

    def _led_brightness(self, guards: DisplayGuards) -> int:
        """Note 12, invariant 8: true off in OFF and whenever night is active,
        regardless of display state."""
        if self._state is DisplayState.OFF or guards.night_active:
            return 0
        if self._illumination_preference == "off":
            return 0
        if self._illumination_preference == "subtle":
            return min(10, self._profile.display.led_brightness)
        return self._profile.display.led_brightness
