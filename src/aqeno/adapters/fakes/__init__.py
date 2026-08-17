"""In-memory fakes for every port, used by tests and the fake-hardware run target.

Each fake implements the same Protocol as its real adapter and is exercised by
the same contract test suite, so it cannot silently drift from reality
(ADR 0008 § 3).
"""

from aqeno.adapters.fakes.audio import FakeAudioEngine
from aqeno.adapters.fakes.persistence import FakeLibrary, FakeSettingsStore

__all__ = ["FakeAudioEngine", "FakeLibrary", "FakeSettingsStore"]
