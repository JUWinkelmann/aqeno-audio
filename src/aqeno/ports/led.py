"""User-facing status LED port — ADR 0016 § 2.

Separate from `DisplayPanel` because the hardware is separate: on Reference
Hardware 1 the LEDs live on the encoder and the NeoKey, not on the panel. Same
policy, because `night_active` and `DISPLAY_STATE_MACHINE.md` note 12 make LED
brightness one decision with the panel's — `application/display.py` computes both.

No colour and no pulse. `PLATFORM_CONTRACTS.md` § LED contract lists both as later
adapter capabilities; nothing in this slice sets either, and an unused parameter
would be a speculative extension point (`AGENTS.md` Code quality).
"""

from __future__ import annotations

from typing import Protocol


class StatusLeds(Protocol):
    def set_brightness(self, level: int) -> None:
        """Logical 0-100. 0 is true off."""
        ...
