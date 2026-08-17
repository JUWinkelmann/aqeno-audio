"""Clock port.

Application code never calls `time.monotonic()`, `time.sleep()`, `datetime.now()` or a
Qt timer directly (ADR 0008 § 4). Everything that measures a duration takes a `Clock`,
so a 30-second timeout is tested in microseconds and deterministically.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Protocol


class Clock(Protocol):
    def now(self) -> float:
        """Monotonic seconds. Only differences are meaningful."""
        ...

    def schedule(self, delay: timedelta, callback: object) -> object:
        """Run `callback` after `delay`. Returns a handle that can be cancelled."""
        ...

    def cancel(self, handle: object) -> None: ...
