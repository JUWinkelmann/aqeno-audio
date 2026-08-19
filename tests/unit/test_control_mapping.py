from __future__ import annotations

from dataclasses import replace

import pytest

from aqeno.adapters.fakes.persistence import FakeSettingsStore
from aqeno.application.control_mapping import MappedInputBus
from aqeno.config.defaults import ControlSettings, default_settings
from aqeno.ports.input import (
    ControlCapability,
    ControlEventType,
    ControlInput,
    ControlType,
    FocusNext,
    FocusPrevious,
    Home,
    LogicalControl,
    Next,
    Previous,
    Select,
    TogglePlayback,
    VolumeDelta,
)


def _button(control: LogicalControl, label: str) -> ControlCapability:
    return ControlCapability(
        control,
        ControlType.BUTTON,
        label,
        (ControlEventType.SHORT_PRESS, ControlEventType.LONG_PRESS),
        True,
    )


def _encoder(control: LogicalControl, label: str, *, illuminated: bool) -> ControlCapability:
    return ControlCapability(
        control,
        ControlType.ROTARY_ENCODER,
        label,
        (
            ControlEventType.ROTATE_LEFT,
            ControlEventType.ROTATE_RIGHT,
            ControlEventType.SHORT_PRESS,
            ControlEventType.LONG_PRESS,
        ),
        illuminated,
    )


class PhysicalSource:
    """RH1: four of the five AQENO controls. SELECT has no hardware yet."""

    def __init__(self) -> None:
        self._listener = None

    @property
    def controls(self) -> tuple[ControlCapability, ...]:
        return (
            _button(LogicalControl.PREVIOUS, "Zurück im Inhalt"),
            _button(LogicalControl.NEXT, "Weiter im Inhalt"),
            _encoder(LogicalControl.VOLUME_ENCODER, "Lautstärke", illuminated=True),
            _button(LogicalControl.HOME, "Startseite"),
        )

    def on_control_input(self, listener: object) -> None:
        self._listener = listener

    def emit(self, control: LogicalControl, event: ControlEventType) -> None:
        assert callable(self._listener)
        self._listener(ControlInput(control, event))


def test_rh1_defaults_map_locally_to_semantic_input() -> None:
    source = PhysicalSource()
    bus = MappedInputBus(source, FakeSettingsStore())
    received = []
    bus.on_input(received.append)

    source.emit(LogicalControl.PREVIOUS, ControlEventType.SHORT_PRESS)
    source.emit(LogicalControl.VOLUME_ENCODER, ControlEventType.ROTATE_LEFT)
    source.emit(LogicalControl.VOLUME_ENCODER, ControlEventType.ROTATE_RIGHT)
    source.emit(LogicalControl.VOLUME_ENCODER, ControlEventType.SHORT_PRESS)
    source.emit(LogicalControl.NEXT, ControlEventType.SHORT_PRESS)
    source.emit(LogicalControl.HOME, ControlEventType.SHORT_PRESS)

    assert received == [
        Previous(),
        VolumeDelta(-1),
        VolumeDelta(1),
        TogglePlayback(),
        Next(),
        Home(),
    ]


def test_custom_mapping_persists_and_reset_restores_defaults() -> None:
    source = PhysicalSource()
    store = FakeSettingsStore()
    bus = MappedInputBus(source, store)
    received = []
    bus.on_input(received.append)

    updated = bus.update_binding(
        LogicalControl.NEXT,
        ControlEventType.SHORT_PRESS,
        "playback.play_pause",
    )
    assert updated.action_id == "playback.play_pause"

    source.emit(LogicalControl.NEXT, ControlEventType.SHORT_PRESS)
    assert received == [TogglePlayback()]

    restarted = MappedInputBus(PhysicalSource(), store)
    assert (
        next(
            item
            for item in restarted.bindings()
            if item.control is LogicalControl.NEXT and item.event is ControlEventType.SHORT_PRESS
        ).action_id
        == "playback.play_pause"
    )

    bus.reset()
    assert (
        next(
            item
            for item in bus.bindings()
            if item.control is LogicalControl.NEXT and item.event is ControlEventType.SHORT_PRESS
        ).action_id
        == "playback.next"
    )


def test_admin_confirmation_uses_fixed_physical_controls_after_remapping() -> None:
    source = PhysicalSource()
    bus = MappedInputBus(source, FakeSettingsStore())
    confirmed = []
    bus.confirmation_inputs.on_input(confirmed.append)
    bus.update_binding(
        LogicalControl.PREVIOUS,
        ControlEventType.SHORT_PRESS,
        "playback.stop",
    )
    bus.update_binding(
        LogicalControl.VOLUME_ENCODER,
        ControlEventType.SHORT_PRESS,
        None,
    )

    source.emit(LogicalControl.PREVIOUS, ControlEventType.SHORT_PRESS)
    source.emit(LogicalControl.VOLUME_ENCODER, ControlEventType.SHORT_PRESS)
    source.emit(LogicalControl.NEXT, ControlEventType.SHORT_PRESS)

    assert confirmed == [Previous(), TogglePlayback(), Next()]


def test_unassigned_and_unsupported_actions_are_not_dispatched() -> None:
    source = PhysicalSource()
    bus = MappedInputBus(source, FakeSettingsStore())
    received = []
    bus.on_input(received.append)

    source.emit(LogicalControl.VOLUME_ENCODER, ControlEventType.LONG_PRESS)
    bus.update_binding(
        LogicalControl.PREVIOUS,
        ControlEventType.SHORT_PRESS,
        None,
    )
    source.emit(LogicalControl.PREVIOUS, ControlEventType.SHORT_PRESS)

    assert received == []


def test_unknown_restored_bindings_are_preserved_but_current_defaults_remain_safe() -> None:
    store = FakeSettingsStore()
    restored = replace(
        default_settings(),
        controls=ControlSettings(
            bindings=("future_dial|triple_press|future.action",),
            illumination="subtle",
        ),
    )
    store.save(restored)
    bus = MappedInputBus(PhysicalSource(), store)

    assert (
        next(
            item
            for item in bus.bindings()
            if item.control is LogicalControl.VOLUME_ENCODER
            and item.event is ControlEventType.SHORT_PRESS
        ).action_id
        == "playback.play_pause"
    )
    assert store.load().controls.bindings == ("future_dial|triple_press|future.action",)


class NavigationSource(PhysicalSource):
    """The complete AQENO control set (ADR 0026 § 2), which RH1 is not yet."""

    @property
    def controls(self) -> tuple[ControlCapability, ...]:
        return (
            _encoder(LogicalControl.SELECT_ENCODER, "Auswahl", illuminated=False),
            *super().controls,
        )


def test_select_encoder_defaults_map_to_navigation_intentions() -> None:
    source = NavigationSource()
    bus = MappedInputBus(source, FakeSettingsStore())
    received = []
    bus.on_input(received.append)

    source.emit(LogicalControl.SELECT_ENCODER, ControlEventType.ROTATE_LEFT)
    source.emit(LogicalControl.SELECT_ENCODER, ControlEventType.ROTATE_RIGHT)
    source.emit(LogicalControl.SELECT_ENCODER, ControlEventType.SHORT_PRESS)

    assert received == [FocusPrevious(), FocusNext(), Select()]


def test_no_default_binds_a_long_press() -> None:
    """ADR 0024 § A2: everyday operation is untimed. The way out is the HOME
    control, not a held button, and nothing else reaches for a long press."""
    bus = MappedInputBus(NavigationSource(), FakeSettingsStore())

    long_press = [
        binding for binding in bus.bindings() if binding.event is ControlEventType.LONG_PRESS
    ]

    assert long_press, "the fixture must actually expose long presses"
    assert all(binding.action_id is None for binding in long_press)


def test_display_wake_cannot_be_bound_to_a_long_press() -> None:
    bus = MappedInputBus(NavigationSource(), FakeSettingsStore())

    wake = next(action for action in bus.actions if action.id == "display.wake")

    assert wake.compatible_events == (ControlEventType.SHORT_PRESS,)
    with pytest.raises(ValueError):
        bus.update_binding(LogicalControl.PREVIOUS, ControlEventType.LONG_PRESS, "display.wake")


def test_volume_encoder_keeps_its_meaning_when_navigation_hardware_exists() -> None:
    """ADR 0024 § 2: volume stays volume. Adding a SELECT control must not
    change what the VOLUME control does in any state."""
    source = NavigationSource()
    bus = MappedInputBus(source, FakeSettingsStore())
    received = []
    bus.on_input(received.append)

    source.emit(LogicalControl.VOLUME_ENCODER, ControlEventType.ROTATE_RIGHT)
    source.emit(LogicalControl.VOLUME_ENCODER, ControlEventType.SHORT_PRESS)

    assert received == [VolumeDelta(1), TogglePlayback()]


def test_rh1_reports_no_select_control_and_stays_operable() -> None:
    """RH1 carries four of the five controls. The SELECT bindings exist in
    settings and are simply not offered — the same honest state as any other
    absent hardware."""
    bus = MappedInputBus(PhysicalSource(), FakeSettingsStore())

    bound = {(item.control, item.event) for item in bus.bindings()}

    assert LogicalControl.SELECT_ENCODER not in {control for control, _ in bound}
    assert "navigation.select" in {action.id for action in bus.actions}
