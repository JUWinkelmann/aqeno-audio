"""Device-wide physical-control mapping.

Hardware emits normalized logical controls.  This module is the only place that
turns them into the small, controlled set of AQENO input intentions.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, replace

from aqeno.config.defaults import ControlSettings, Settings
from aqeno.ports.input import (
    ControlCapability,
    ControlEventType,
    ControlInput,
    FocusNext,
    FocusPrevious,
    Home,
    InputEvent,
    InputListener,
    LogicalControl,
    Next,
    Pause,
    PhysicalInputSource,
    Play,
    Previous,
    Select,
    Stop,
    TogglePlayback,
    VolumeDelta,
    WakeRequest,
)
from aqeno.ports.persistence import SettingsStore


@dataclass(frozen=True, slots=True)
class ControlAction:
    id: str
    label: str
    category: str
    compatible_events: tuple[ControlEventType, ...]


@dataclass(frozen=True, slots=True)
class ControlBinding:
    control: LogicalControl
    event: ControlEventType
    action_id: str | None
    supported: bool = True


_PRESS_EVENTS = (ControlEventType.SHORT_PRESS, ControlEventType.LONG_PRESS)
_ROTATE_EVENTS = (ControlEventType.ROTATE_LEFT, ControlEventType.ROTATE_RIGHT)

CONTROL_ACTIONS: tuple[ControlAction, ...] = (
    ControlAction("playback.play_pause", "Play / Pause", "playback", _PRESS_EVENTS),
    ControlAction("playback.play", "Wiedergabe starten", "playback", _PRESS_EVENTS),
    ControlAction("playback.pause", "Wiedergabe pausieren", "playback", _PRESS_EVENTS),
    ControlAction("playback.stop", "Wiedergabe stoppen", "playback", _PRESS_EVENTS),
    ControlAction("playback.previous", "Vorheriger Titel", "playback", _PRESS_EVENTS),
    ControlAction("playback.next", "Nächster Titel", "playback", _PRESS_EVENTS),
    ControlAction("volume.down", "Leiser", "volume", _ROTATE_EVENTS + _PRESS_EVENTS),
    ControlAction("volume.up", "Lauter", "volume", _ROTATE_EVENTS + _PRESS_EVENTS),
    # Short press only: with navigation waking the panel, nothing needs a
    # long-press wake, and everyday operation may not depend on a timed gesture
    # (ADR 0024 § A2, § A4).
    ControlAction("display.wake", "Display aktivieren", "display", (ControlEventType.SHORT_PRESS,)),
    # Navigation (ADR 0024, ADR 0026). Rotation moves focus; a press activates
    # it. These are ordinary registry entries, so a Manager may bind them to any
    # control a source reports — but never onto the control that carries volume.
    ControlAction(
        "navigation.focus_previous", "Auswahl zurück", "navigation", _ROTATE_EVENTS + _PRESS_EVENTS
    ),
    ControlAction(
        "navigation.focus_next", "Auswahl weiter", "navigation", _ROTATE_EVENTS + _PRESS_EVENTS
    ),
    ControlAction("navigation.select", "Auswählen", "navigation", _PRESS_EVENTS),
    # HOME (ADR 0026 § 4). There is no back action, because there is no back
    # control: HOME is the one always-available way out, in every state.
    ControlAction("navigation.home", "Startseite", "navigation", _PRESS_EVENTS),
)
_ACTIONS_BY_ID = {action.id: action for action in CONTROL_ACTIONS}


def _binding_text(control: LogicalControl, event: ControlEventType, action_id: str | None) -> str:
    return "|".join((control.value, event.value, action_id or ""))


def parse_binding(raw: str) -> ControlBinding | None:
    parts = raw.split("|", 2)
    if len(parts) != 3:
        return None
    try:
        control = LogicalControl(parts[0])
        event = ControlEventType(parts[1])
    except ValueError:
        # A mapping restored from another supported hardware generation is kept
        # in Settings but is not executable by this runtime.
        return None
    action_id = parts[2] or None
    return ControlBinding(
        control=control,
        event=event,
        action_id=action_id,
        supported=action_id is None or action_id in _ACTIONS_BY_ID,
    )


class MappedInputBus:
    """Map one physical source locally and expose the existing semantic InputBus."""

    def __init__(self, source: PhysicalInputSource, settings_store: SettingsStore) -> None:
        self._source = source
        self._settings_store = settings_store
        self._listeners: list[InputListener] = []
        self._confirmation_listeners: list[InputListener] = []
        self._lock = threading.RLock()
        self._settings = settings_store.load()
        source.on_control_input(self._handle_control)

    @property
    def confirmation_inputs(self) -> _PhysicalConfirmationInputs:
        """Fixed physical ownership proof, independent from user mappings.

        Changing a playback binding must never make local Admin setup or
        recovery impossible.  The confirmation sequence therefore observes the
        PREVIOUS → VOLUME → NEXT short presses by logical control identity,
        before action mapping, while still using the ordinary in-process
        ``InputBus`` shape.  Those three identities are permanent (ADR 0026 § 2),
        so the sequence carries over to target hardware unchanged.
        """
        return _PhysicalConfirmationInputs(self)

    @property
    def controls(self) -> tuple[ControlCapability, ...]:
        return self._source.controls

    @property
    def actions(self) -> tuple[ControlAction, ...]:
        return CONTROL_ACTIONS

    @property
    def illumination(self) -> str:
        return self._settings.controls.illumination

    def on_input(self, listener: InputListener) -> None:
        with self._lock:
            self._listeners.append(listener)

    def start(self) -> None:
        start = getattr(self._source, "start", None)
        if start is not None:
            start()

    def close(self) -> None:
        close = getattr(self._source, "close", None)
        if close is not None:
            close()

    def bindings(self) -> tuple[ControlBinding, ...]:
        configured: dict[tuple[LogicalControl, ControlEventType], ControlBinding] = {}
        # Missing current-device entries use the validated RH1 defaults. An
        # explicitly unassigned entry is encoded with an empty action and still
        # overrides that default. Unknown future-hardware entries remain in the
        # settings file but cannot leave today's primary controls unusable.
        for raw in ControlSettings().bindings:
            binding = parse_binding(raw)
            if binding is not None:
                configured[(binding.control, binding.event)] = binding
        for raw in self._settings.controls.bindings:
            binding = parse_binding(raw)
            if binding is not None:
                configured[(binding.control, binding.event)] = binding
        return tuple(
            configured.get(
                (capability.control, event),
                ControlBinding(capability.control, event, None),
            )
            for capability in self.controls
            for event in capability.events
        )

    def update_binding(
        self,
        control: LogicalControl,
        event: ControlEventType,
        action_id: str | None,
    ) -> ControlBinding:
        capability = next((item for item in self.controls if item.control is control), None)
        if capability is None or event not in capability.events:
            raise ValueError("control event is not available on this device")
        action = _ACTIONS_BY_ID.get(action_id) if action_id is not None else None
        if action_id is not None and action is None:
            raise ValueError("action is not supported by this AQENO version")
        if action is not None and event not in action.compatible_events:
            raise ValueError("action is not compatible with this control event")

        with self._lock:
            key = (control.value, event.value)
            retained = [
                raw
                for raw in self._settings.controls.bindings
                if tuple(raw.split("|", 2)[:2]) != key
            ]
            retained.append(_binding_text(control, event, action_id))
            controls = replace(self._settings.controls, bindings=tuple(retained))
            self._settings = replace(self._settings, controls=controls)
            self._settings_store.save(self._settings)
        return ControlBinding(control, event, action_id)

    def reset(self) -> tuple[ControlBinding, ...]:
        with self._lock:
            controls = ControlSettings()
            self._settings = replace(self._settings, controls=controls)
            self._settings_store.save(self._settings)
        return self.bindings()

    def set_illumination(self, value: str) -> None:
        if value not in {"off", "subtle", "clear"}:
            raise ValueError("unsupported illumination preference")
        with self._lock:
            controls = replace(self._settings.controls, illumination=value)
            self._settings = replace(self._settings, controls=controls)
            self._settings_store.save(self._settings)

    def replace_settings(self, settings: Settings) -> None:
        with self._lock:
            self._settings = settings

    def _handle_control(self, physical: ControlInput) -> None:
        confirmation_event = _confirmation_event(physical)
        if confirmation_event is not None:
            with self._lock:
                confirmation_listeners = tuple(self._confirmation_listeners)
            for listener in confirmation_listeners:
                listener(confirmation_event)

        binding = next(
            (
                item
                for item in self.bindings()
                if item.control is physical.control and item.event is physical.event
            ),
            None,
        )
        if binding is None or binding.action_id is None or not binding.supported:
            return
        event = _semantic_event(binding.action_id)
        if event is None:
            return
        with self._lock:
            listeners = tuple(self._listeners)
        for listener in listeners:
            listener(event)


class _PhysicalConfirmationInputs:
    """Read-only InputBus view used only by the local ownership flow."""

    def __init__(self, controls: MappedInputBus) -> None:
        self._controls = controls

    def on_input(self, listener: InputListener) -> None:
        with self._controls._lock:
            self._controls._confirmation_listeners.append(listener)


def _confirmation_event(physical: ControlInput) -> InputEvent | None:
    if physical.event is not ControlEventType.SHORT_PRESS:
        return None
    if physical.control is LogicalControl.PREVIOUS:
        return Previous()
    if physical.control is LogicalControl.VOLUME_ENCODER:
        return TogglePlayback()
    if physical.control is LogicalControl.NEXT:
        return Next()
    return None


def _semantic_event(action_id: str) -> InputEvent | None:
    if action_id == "playback.play_pause":
        return TogglePlayback()
    if action_id == "playback.play":
        return Play()
    if action_id == "playback.pause":
        return Pause()
    if action_id == "playback.stop":
        return Stop()
    if action_id == "playback.previous":
        return Previous()
    if action_id == "playback.next":
        return Next()
    if action_id == "volume.down":
        return VolumeDelta(-1)
    if action_id == "volume.up":
        return VolumeDelta(1)
    if action_id == "display.wake":
        return WakeRequest()
    if action_id == "navigation.focus_previous":
        return FocusPrevious()
    if action_id == "navigation.focus_next":
        return FocusNext()
    if action_id == "navigation.select":
        return Select()
    if action_id == "navigation.home":
        return Home()
    return None
