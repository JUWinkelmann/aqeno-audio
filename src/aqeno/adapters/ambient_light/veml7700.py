"""Vishay VEML7700 adapter using a supplied 16-bit register bus.

The surrounding RH1 adapter will own the concrete Linux I2C library. Keeping
that choice out of this module avoids adding a dependency before the assembled
hardware proves which bus implementation is appropriate.
"""

from __future__ import annotations

from typing import Protocol


class WordRegisterBus(Protocol):
    def write_word_data(self, address: int, register: int, value: int) -> None: ...

    def read_word_data(self, address: int, register: int) -> int: ...


class Veml7700:
    """100 ms integration at 1/8 gain for the RH1 feasibility range.

    Register values and the 0.5376 lx/count resolution follow Vishay document
    84286, VEML7700 datasheet revision 1.8.
    """

    ADDRESS = 0x10
    _CONFIGURATION = 0x00
    _ALS_DATA = 0x04
    _GAIN_ONE_EIGHTH_100_MS = 0x1000
    _LUX_PER_COUNT = 0.5376

    def __init__(self, bus: WordRegisterBus, *, address: int = ADDRESS) -> None:
        self._bus = bus
        self._address = address
        bus.write_word_data(address, self._CONFIGURATION, self._GAIN_ONE_EIGHTH_100_MS)

    def read_lux(self) -> float:
        counts = self._bus.read_word_data(self._address, self._ALS_DATA)
        return max(0.0, min(0xFFFF, counts)) * self._LUX_PER_COUNT
