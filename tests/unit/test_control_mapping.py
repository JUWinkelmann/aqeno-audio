from __future__ import annotations

from dataclasses import replace

from aqeno.adapters.fakes.persistence import FakeSettingsStore
from aqeno.application.control_mapping import MappedInputBus
from aqeno.config.defaults import ControlSettings, default_settings
from aqeno.ports.input import (
    ControlCapability,
    ControlEventType,
    ControlInput,
    ControlType,
    LogicalControl,
    Next,
    Previous,
    TogglePlayback,
    VolumeDelta,
)


class PhysicalSource:
    def __init__(self) -> None:
        self._listener = None

    @property
    def controls(self) -> tuple[ControlCapability, ...]:
        return (
            ControlCapability(
                LogicalControl.PRIMARY_LEFT,
                ControlType.BUTTON,
                "Linke Taste",
                (ControlEventType.SHORT_PRESS, ControlEventType.LONG_PRESS),
                True,
            ),
            ControlCapability(
                LogicalControl.PRIMARY_ENCODER,
                ControlType.ROTARY_ENCODER,
                "Drehknopf",
                (
                    ControlEventType.ROTATE_LEFT,
                    ControlEventType.ROTATE_RIGHT,
                    ControlEventType.SHORT_PRESS,
                    ControlEventType.LONG_PRESS,
                ),
                True,
            ),
            ControlCapability(
                LogicalControl.PRIMARY_RIGHT,
                ControlType.BUTTON,
                "Rechte Taste",
                (ControlEventType.SHORT_PRESS, ControlEventType.LONG_PRESS),
                True,
            ),
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

    source.emit(LogicalControl.PRIMARY_LEFT, ControlEventType.SHORT_PRESS)
    source.emit(LogicalControl.PRIMARY_ENCODER, ControlEventType.ROTATE_LEFT)
    source.emit(LogicalControl.PRIMARY_ENCODER, ControlEventType.ROTATE_RIGHT)
    source.emit(LogicalControl.PRIMARY_ENCODER, ControlEventType.SHORT_PRESS)
    source.emit(LogicalControl.PRIMARY_RIGHT, ControlEventType.SHORT_PRESS)

    assert received == [
        Previous(),
        VolumeDelta(-1),
        VolumeDelta(1),
        TogglePlayback(),
        Next(),
    ]


def test_custom_mapping_persists_and_reset_restores_defaults() -> None:
    source = PhysicalSource()
    store = FakeSettingsStore()
    bus = MappedInputBus(source, store)
    received = []
    bus.on_input(received.append)

    updated = bus.update_binding(
        LogicalControl.PRIMARY_RIGHT,
        ControlEventType.SHORT_PRESS,
        "playback.play_pause",
    )
    assert updated.action_id == "playback.play_pause"

    source.emit(LogicalControl.PRIMARY_RIGHT, ControlEventType.SHORT_PRESS)
    assert received == [TogglePlayback()]

    restarted = MappedInputBus(PhysicalSource(), store)
    assert (
        next(
            item
            for item in restarted.bindings()
            if item.control is LogicalControl.PRIMARY_RIGHT
            and item.event is ControlEventType.SHORT_PRESS
        ).action_id
        == "playback.play_pause"
    )

    bus.reset()
    assert (
        next(
            item
            for item in bus.bindings()
            if item.control is LogicalControl.PRIMARY_RIGHT
            and item.event is ControlEventType.SHORT_PRESS
        ).action_id
        == "playback.next"
    )


def test_admin_confirmation_uses_fixed_physical_controls_after_remapping() -> None:
    source = PhysicalSource()
    bus = MappedInputBus(source, FakeSettingsStore())
    confirmed = []
    bus.confirmation_inputs.on_input(confirmed.append)
    bus.update_binding(
        LogicalControl.PRIMARY_LEFT,
        ControlEventType.SHORT_PRESS,
        "playback.stop",
    )
    bus.update_binding(
        LogicalControl.PRIMARY_ENCODER,
        ControlEventType.SHORT_PRESS,
        None,
    )

    source.emit(LogicalControl.PRIMARY_LEFT, ControlEventType.SHORT_PRESS)
    source.emit(LogicalControl.PRIMARY_ENCODER, ControlEventType.SHORT_PRESS)
    source.emit(LogicalControl.PRIMARY_RIGHT, ControlEventType.SHORT_PRESS)

    assert confirmed == [Previous(), TogglePlayback(), Next()]


def test_unassigned_and_unsupported_actions_are_not_dispatched() -> None:
    source = PhysicalSource()
    bus = MappedInputBus(source, FakeSettingsStore())
    received = []
    bus.on_input(received.append)

    source.emit(LogicalControl.PRIMARY_ENCODER, ControlEventType.LONG_PRESS)
    bus.update_binding(
        LogicalControl.PRIMARY_LEFT,
        ControlEventType.SHORT_PRESS,
        None,
    )
    source.emit(LogicalControl.PRIMARY_LEFT, ControlEventType.SHORT_PRESS)

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
            if item.control is LogicalControl.PRIMARY_ENCODER
            and item.event is ControlEventType.SHORT_PRESS
        ).action_id
        == "playback.play_pause"
    )
    assert store.load().controls.bindings == ("future_dial|triple_press|future.action",)
