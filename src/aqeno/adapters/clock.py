"""System clock used by the running AQENO application."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from datetime import timedelta


class SystemClock:
    def now(self) -> float:
        return time.monotonic()

    def schedule(self, delay: timedelta, callback: Callable[[], None]) -> object:
        timer = threading.Timer(delay.total_seconds(), callback)
        timer.daemon = True
        timer.start()
        return timer

    def cancel(self, handle: object) -> None:
        if not isinstance(handle, threading.Timer):
            raise TypeError("SystemClock can only cancel its own timer handles")
        handle.cancel()
