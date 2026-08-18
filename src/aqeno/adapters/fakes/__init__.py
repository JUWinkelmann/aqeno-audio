"""In-memory fakes for every port, used by tests and the fake-hardware run target.

Each fake implements the same Protocol as its real adapter and is exercised by
the same contract test suite, so it cannot silently drift from reality
(ADR 0008 § 3).
"""

from aqeno.adapters.fakes.audio import FakeAudioEngine
from aqeno.adapters.fakes.clock import FakeClock
from aqeno.adapters.fakes.display import FakeDisplayPanel
from aqeno.adapters.fakes.input import FakeInputBus
from aqeno.adapters.fakes.led import FakeStatusLeds
from aqeno.adapters.fakes.metadata import FakeMediaProbe
from aqeno.adapters.fakes.persistence import FakeLibrary, FakeSettingsStore

__all__ = [
    "FakeAudioEngine",
    "FakeClock",
    "FakeDisplayPanel",
    "FakeInputBus",
    "FakeLibrary",
    "FakeMediaProbe",
    "FakeSettingsStore",
    "FakeStatusLeds",
]
