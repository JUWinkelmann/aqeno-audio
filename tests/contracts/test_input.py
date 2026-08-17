"""Input delivery contract shared by the fake bus and keyboard simulator."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from aqeno.adapters.fakes import FakeInputBus
from aqeno.adapters.input import KeyboardSimulator
from aqeno.ports.input import InputBus, InputEvent, VolumeDelta


@pytest.fixture(params=["fake", "keyboard"])
def input_bus(request: pytest.FixtureRequest) -> tuple[InputBus, Callable[[InputEvent], None]]:
    if request.param == "fake":
        bus = FakeInputBus()
        return bus, bus.emit

    keyboard = KeyboardSimulator()

    def emit(event: InputEvent) -> None:
        assert isinstance(event, VolumeDelta)
        key = "up" if event.delta > 0 else "down"
        assert keyboard.handle_key(key)

    return keyboard, emit


def test_delivers_each_event_in_registration_order(
    input_bus: tuple[InputBus, Callable[[InputEvent], None]],
) -> None:
    bus, emit = input_bus
    received: list[tuple[str, InputEvent]] = []
    bus.on_input(lambda event: received.append(("first", event)))
    bus.on_input(lambda event: received.append(("second", event)))

    emit(VolumeDelta(1))
    emit(VolumeDelta(1))

    assert received == [
        ("first", VolumeDelta(1)),
        ("second", VolumeDelta(1)),
        ("first", VolumeDelta(1)),
        ("second", VolumeDelta(1)),
    ]


def test_does_not_replay_input_to_late_listener(
    input_bus: tuple[InputBus, Callable[[InputEvent], None]],
) -> None:
    bus, emit = input_bus
    emit(VolumeDelta(1))
    received: list[InputEvent] = []

    bus.on_input(received.append)

    assert received == []


def test_listener_failure_stops_delivery(
    input_bus: tuple[InputBus, Callable[[InputEvent], None]],
) -> None:
    bus, emit = input_bus
    reached_later_listener = False

    def fail(_event: InputEvent) -> None:
        raise RuntimeError("input handler failed")

    def later_listener(_event: InputEvent) -> None:
        nonlocal reached_later_listener
        reached_later_listener = True

    bus.on_input(fail)
    bus.on_input(later_listener)

    with pytest.raises(RuntimeError, match="input handler failed"):
        emit(VolumeDelta(1))

    assert not reached_later_listener
