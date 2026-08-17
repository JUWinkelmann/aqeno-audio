from __future__ import annotations

from datetime import timedelta
from typing import ClassVar

import pytest

from aqeno.adapters.clock import SystemClock


class RecordedTimer:
    created: ClassVar[list[RecordedTimer]] = []

    def __init__(self, interval: float, callback: object) -> None:
        self.interval = interval
        self.callback = callback
        self.daemon = False
        self.started = False
        self.cancelled = False
        self.created.append(self)

    def start(self) -> None:
        self.started = True

    def cancel(self) -> None:
        self.cancelled = True


def test_schedules_daemon_timer(monkeypatch: pytest.MonkeyPatch) -> None:
    RecordedTimer.created.clear()
    monkeypatch.setattr("aqeno.adapters.clock.threading.Timer", RecordedTimer)

    def callback() -> None:
        pass

    clock = SystemClock()

    handle = clock.schedule(timedelta(seconds=2.5), callback)

    assert handle is RecordedTimer.created[0]
    assert handle.interval == 2.5
    assert handle.callback is callback
    assert handle.daemon
    assert handle.started

    clock.cancel(handle)
    assert handle.cancelled


def test_cancel_rejects_foreign_handle() -> None:
    with pytest.raises(TypeError, match="own timer handles"):
        SystemClock().cancel(object())
