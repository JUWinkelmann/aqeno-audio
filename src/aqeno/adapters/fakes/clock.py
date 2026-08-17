from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta


class FakeClock:
    """Deterministic monotonic clock for application and scenario tests."""

    def __init__(self, start: float = 0.0) -> None:
        self._now = start
        self._scheduled: list[tuple[float, Callable[[], None], int]] = []
        self._next_handle = 0

    def now(self) -> float:
        return self._now

    def schedule(self, delay: timedelta, callback: Callable[[], None]) -> object:
        self._next_handle += 1
        handle = self._next_handle
        self._scheduled.append((self._now + delay.total_seconds(), callback, handle))
        return handle

    def cancel(self, handle: object) -> None:
        self._scheduled = [item for item in self._scheduled if item[2] != handle]

    def advance(self, delta: timedelta) -> None:
        target = self._now + delta.total_seconds()
        while True:
            due = min(
                (item for item in self._scheduled if item[0] <= target),
                key=lambda item: (item[0], item[2]),
                default=None,
            )
            if due is None:
                break
            self._scheduled.remove(due)
            self._now = due[0]
            due[1]()
        self._now = target

    @property
    def pending(self) -> int:
        return len(self._scheduled)
