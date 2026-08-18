from __future__ import annotations

import pytest

from aqeno.adapters.ambient_light.veml7700 import Veml7700


class RegisterBus:
    def __init__(self, reading: int) -> None:
        self.reading = reading
        self.writes: list[tuple[int, int, int]] = []

    def write_word_data(self, address: int, register: int, value: int) -> None:
        self.writes.append((address, register, value))

    def read_word_data(self, address: int, register: int) -> int:
        assert (address, register) == (0x10, 0x04)
        return self.reading


def test_configures_one_eighth_gain_and_converts_counts_to_lux() -> None:
    bus = RegisterBus(reading=100)
    sensor = Veml7700(bus)

    assert bus.writes == [(0x10, 0x00, 0x1000)]
    assert sensor.read_lux() == pytest.approx(53.76)


def test_invalid_bus_value_is_bounded_to_sensor_range() -> None:
    assert Veml7700(RegisterBus(reading=-1)).read_lux() == 0.0
    assert Veml7700(RegisterBus(reading=0x1FFFF)).read_lux() == pytest.approx(0xFFFF * 0.5376)
