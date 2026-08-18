"""Readiness ladder — `docs/implementation/READINESS_STATES.md`.

Readiness answers *what has become available since power-on*, not what is currently
impaired (that is `FAILURE_STATES.md`, an orthogonal axis, § 6). The ladder is
monotonic (§ 1): once a rung is reached it is never revoked, even when an adapter
degrades afterwards. `__main__.py` is the only caller that advances it, because the
composition root is the only place that knows which adapters exist (§ 8).
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from enum import IntEnum, auto

from aqeno.ports.clock import Clock

logger = logging.getLogger(__name__)


class ReadinessState(IntEnum):
    """Ordered so `current >= state` answers "has this rung been reached"."""

    BOOTING = auto()
    LOCAL_READY = auto()
    PLAYBACK_READY = auto()
    UI_READY = auto()
    NETWORK_READY = auto()
    OPTIONAL_SERVICES_READY = auto()


ReadinessListener = Callable[[], None]


class Readiness:
    """The current rung, reached in order, logged once each with a monotonic
    timestamp (§ 7), and never revoked.

    Advancing to a rung at or before the current one is a programming error, not a
    state change (§ 1) — it raises rather than silently ignoring or regressing.
    """

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._current = ReadinessState.BOOTING
        self._listeners: dict[ReadinessState, list[ReadinessListener]] = defaultdict(list)
        self._log(ReadinessState.BOOTING)

    @property
    def current(self) -> ReadinessState:
        return self._current

    def has_reached(self, state: ReadinessState) -> bool:
        return self._current >= state

    def advance(self, state: ReadinessState) -> None:
        if state <= self._current:
            raise AssertionError(
                f"readiness cannot move from {self._current.name} to {state.name}: "
                "the ladder only advances (READINESS_STATES.md § 1)"
            )
        self._current = state
        self._log(state)
        for listener in self._listeners.pop(state, []):
            listener()

    def on_reached(self, state: ReadinessState, listener: ReadinessListener) -> None:
        """Call `listener` once `state` is reached — immediately if it already has
        been, since the ladder never regresses (so "not yet reached" cannot become
        true again after this call).

        This is where the display service's pending-wake flag and, later, the
        ingestion scan hook in (§ 8): a rung-scoped callback rather than a generic
        subscription, since nothing needs to know about every rung.
        """
        if self.has_reached(state):
            listener()
        else:
            self._listeners[state].append(listener)

    def _log(self, state: ReadinessState) -> None:
        logger.info("readiness reached %s", state.name, extra={"monotonic": self._clock.now()})
