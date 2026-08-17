"""Shared test fixtures.

Two rules from ADR 0008 that are easy to break and hard to notice:
  - no `time.sleep()` anywhere in tests; advance `FakeClock` instead;
  - no audio files in the repository; fixtures are generated at test time.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import timedelta
from pathlib import Path

import pytest


class FakeClock:
    """Deterministic monotonic time. A 30-second timeout is tested in microseconds."""

    def __init__(self, start: float = 0.0) -> None:
        self._now = start
        self._scheduled: list[tuple[float, object, int]] = []
        self._next_handle = 0

    def now(self) -> float:
        return self._now

    def schedule(self, delay: timedelta, callback: object) -> object:
        self._next_handle += 1
        handle = self._next_handle
        self._scheduled.append((self._now + delay.total_seconds(), callback, handle))
        return handle

    def cancel(self, handle: object) -> None:
        self._scheduled = [item for item in self._scheduled if item[2] != handle]

    def advance(self, delta: timedelta) -> list[object]:
        """Move time forward and return the callbacks that became due, in order."""
        target = self._now + delta.total_seconds()
        due = sorted((item for item in self._scheduled if item[0] <= target), key=lambda i: i[0])
        self._scheduled = [item for item in self._scheduled if item[0] > target]
        self._now = target
        return [callback for _, callback, _ in due]

    @property
    def pending(self) -> int:
        return len(self._scheduled)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def aqeno_state_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Point every AQENO location at a temporary directory (ADR 0007 § 4).

    Tests must never touch real device state.
    """
    for variable in ("AQENO_CONFIG_DIR", "AQENO_DATA_DIR", "AQENO_STATE_DIR"):
        monkeypatch.setenv(variable, str(tmp_path / variable.lower()))
    yield tmp_path
