"""Ambient-light hardware boundary — ADR 0017."""

from __future__ import annotations

from typing import Protocol


class AmbientLight(Protocol):
    def read_lux(self) -> float:
        """Return current illuminance in lux."""
        ...
