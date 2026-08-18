from __future__ import annotations

import threading
from dataclasses import dataclass

import pytest

from aqeno.adapters.input.i2c_seesaw import I2cSeesawInputBus
from aqeno.ports.input import Next, Previous, TogglePlayback, VolumeDelta


@dataclass
class Encoder:
    current: int = 0
    is_pressed: bool = False

    def position(self) -> int:
        return self.current

    def pressed(self) -> bool:
        return self.is_pressed


@dataclass
class Keys:
    current: tuple[bool, ...] = (False, False, False, False)

    def pressed_keys(self) -> tuple[bool, ...]:
        return self.current


def test_first_sample_sets_baselines_without_emitting() -> None:
    encoder = Encoder(current=10, is_pressed=True)
    keys = Keys((True, False, False, False))
    bus = I2cSeesawInputBus(encoder=encoder, keys=keys)
    received = []
    bus.on_input(received.append)

    bus.poll_once()

    assert received == []


def test_encoder_delta_is_full_and_clockwise_positive() -> None:
    encoder = Encoder(current=4)
    bus = I2cSeesawInputBus(encoder=encoder, keys=Keys())
    received = []
    bus.on_input(received.append)

    bus.poll_once()
    encoder.current = 1
    bus.poll_once()
    encoder.current = 6
    bus.poll_once()

    assert received == [VolumeDelta(3), VolumeDelta(-5)]


def test_button_and_supported_keys_emit_only_on_press_edges() -> None:
    encoder = Encoder()
    keys = Keys()
    bus = I2cSeesawInputBus(encoder=encoder, keys=keys)
    received = []
    bus.on_input(received.append)

    bus.poll_once()
    encoder.is_pressed = True
    keys.current = (True, False, True, True)
    bus.poll_once()
    bus.poll_once()
    encoder.is_pressed = False
    keys.current = (False, False, False, False)
    bus.poll_once()
    encoder.is_pressed = True
    keys.current = (True, False, False, False)
    bus.poll_once()

    assert received == [TogglePlayback(), Previous(), Next(), TogglePlayback(), Previous()]


def test_listener_order_is_synchronous_and_registration_does_not_replay() -> None:
    encoder = Encoder()
    bus = I2cSeesawInputBus(encoder=encoder, keys=Keys())
    received: list[tuple[str, object]] = []
    bus.on_input(lambda event: received.append(("first", event)))

    bus.poll_once()
    encoder.current = 2
    bus.poll_once()

    bus.on_input(lambda event: received.append(("second", event)))
    encoder.current = 3
    bus.poll_once()

    assert received == [
        ("first", VolumeDelta(-2)),
        ("first", VolumeDelta(-1)),
        ("second", VolumeDelta(-1)),
    ]


def test_listener_failure_stops_synchronous_delivery() -> None:
    encoder = Encoder()
    bus = I2cSeesawInputBus(encoder=encoder, keys=Keys())
    reached_later_listener = False

    def fail(event: object) -> None:
        raise RuntimeError("input handler failed")

    def later(event: object) -> None:
        nonlocal reached_later_listener
        reached_later_listener = True

    bus.on_input(fail)
    bus.on_input(later)
    bus.poll_once()
    encoder.current = 1

    with pytest.raises(RuntimeError, match="input handler failed"):
        bus.poll_once()

    assert not reached_later_listener


def test_start_does_not_read_until_after_construction_and_close_stops_thread() -> None:
    encoder = Encoder()
    keys = Keys()
    reads = 0
    sampled = threading.Event()

    class ReadingEncoder(Encoder):
        def position(self) -> int:
            nonlocal reads
            reads += 1
            sampled.set()
            return super().position()

    encoder = ReadingEncoder()
    bus = I2cSeesawInputBus(encoder=encoder, keys=keys, poll_interval=0.001)
    assert reads == 0

    bus.start()
    assert sampled.wait(timeout=1)
    bus.close()

    assert reads >= 1
