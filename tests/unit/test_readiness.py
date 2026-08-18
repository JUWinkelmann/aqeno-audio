"""Named tests for `READINESS_STATES.md` § 9's invariants."""

from __future__ import annotations

import logging
from datetime import timedelta

import pytest

from aqeno.adapters.fakes import FakeClock
from aqeno.application.readiness import Readiness, ReadinessState


def test_booting_is_reached_at_construction() -> None:
    """§ 2: BOOTING is reached at process start."""
    readiness = Readiness(FakeClock())
    assert readiness.current is ReadinessState.BOOTING


def test_the_ladder_never_moves_backwards() -> None:
    """Invariant 1."""
    readiness = Readiness(FakeClock())
    readiness.advance(ReadinessState.LOCAL_READY)
    readiness.advance(ReadinessState.PLAYBACK_READY)

    with pytest.raises(AssertionError):
        readiness.advance(ReadinessState.LOCAL_READY)
    with pytest.raises(AssertionError):
        readiness.advance(ReadinessState.PLAYBACK_READY)  # re-announcing the same rung

    assert readiness.current is ReadinessState.PLAYBACK_READY


def test_a_rung_whose_criteria_never_run_is_simply_never_reached() -> None:
    """§ 1: later rungs do not become reachable by skipping it."""
    readiness = Readiness(FakeClock())
    readiness.advance(ReadinessState.LOCAL_READY)
    assert not readiness.has_reached(ReadinessState.PLAYBACK_READY)
    assert not readiness.has_reached(ReadinessState.UI_READY)


def test_on_reached_fires_once_when_the_rung_arrives() -> None:
    readiness = Readiness(FakeClock())
    calls: list[str] = []
    readiness.on_reached(ReadinessState.LOCAL_READY, lambda: calls.append("local"))

    readiness.advance(ReadinessState.LOCAL_READY)
    assert calls == ["local"]

    readiness.advance(ReadinessState.PLAYBACK_READY)
    assert calls == ["local"], "a listener for one rung must not fire again for a later one"


def test_on_reached_fires_immediately_when_already_reached() -> None:
    """The ladder never regresses, so a late registration for an already-reached
    rung must not wait for an advance that will never happen."""
    readiness = Readiness(FakeClock())
    readiness.advance(ReadinessState.LOCAL_READY)

    calls: list[str] = []
    readiness.on_reached(ReadinessState.LOCAL_READY, lambda: calls.append("local"))
    assert calls == ["local"]


def test_nothing_waits_on_network_ready() -> None:
    """Invariant 3 (the ladder-level half; the local-playback half is
    `tests/scenarios/test_dark_room.py` and `test_startup.py`). Stopping the ladder
    at PLAYBACK_READY must not raise or block — there is no code anywhere that
    awaits a later rung to keep running."""
    readiness = Readiness(FakeClock())
    readiness.advance(ReadinessState.LOCAL_READY)
    readiness.advance(ReadinessState.PLAYBACK_READY)
    assert readiness.current is ReadinessState.PLAYBACK_READY
    assert not readiness.has_reached(ReadinessState.NETWORK_READY)


def test_a_failed_rung_leaves_the_process_at_the_last_one_reached() -> None:
    """Invariant 6, in miniature: a rung that is never reached (its entry criteria
    failed, e.g. `BOOTING` for a corrupt database) must not silently unblock a
    later one, and the process must not be forced to exit — nothing here raises
    merely because the ladder stalled."""
    readiness = Readiness(FakeClock())
    assert readiness.current is ReadinessState.BOOTING
    assert not readiness.has_reached(ReadinessState.LOCAL_READY)


def test_each_rung_is_logged_once_with_a_monotonic_timestamp_in_order(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Invariant 10."""
    clock = FakeClock()
    with caplog.at_level(logging.INFO, logger="aqeno.application.readiness"):
        readiness = Readiness(clock)
        clock.advance(timedelta(seconds=1))
        readiness.advance(ReadinessState.LOCAL_READY)
        clock.advance(timedelta(seconds=1))
        readiness.advance(ReadinessState.PLAYBACK_READY)

    records = [r for r in caplog.records if r.name == "aqeno.application.readiness"]
    assert [r.getMessage() for r in records] == [
        "readiness reached BOOTING",
        "readiness reached LOCAL_READY",
        "readiness reached PLAYBACK_READY",
    ]
    timestamps = [r.monotonic for r in records]  # type: ignore[attr-defined]
    assert timestamps == sorted(timestamps)
    assert timestamps == [0.0, 1.0, 2.0]
