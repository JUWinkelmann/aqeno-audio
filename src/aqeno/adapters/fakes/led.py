"""Recording fake `StatusLeds` — lets a test assert the exact brightness sequence
applied to user-facing LEDs, in particular that `night_active` and `OFF` force
true zero (`DISPLAY_STATE_MACHINE.md` note 12, invariant 8)."""

from __future__ import annotations


class FakeStatusLeds:
    def __init__(self) -> None:
        self.calls: list[int] = []
        self.brightness = 0

    def set_brightness(self, level: int) -> None:
        self.brightness = level
        self.calls.append(level)
