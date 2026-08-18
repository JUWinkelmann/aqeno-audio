"""Display panel port — ADR 0016 § 1, amending `PLATFORM_CONTRACTS.md` § Display contract.

Carries panel power and a resolved brightness, not a logical display state. The
state machine (`domain/display.py`) already resolves state and guards to a
brightness; an adapter that instead received `DIM` would need its own copy of
profile-dependent brightness policy, and two adapters would drift. The adapter
emits and applies; it never decides (`AGENTS.md` Architecture rules).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

TouchListener = Callable[[], None]


@dataclass(frozen=True, slots=True)
class PanelCapabilities:
    authoritative_off: bool
    """Whether `set_power(False)` truly stops the panel emitting light, rather than
    only zeroing the backlight on a panel that keeps scanning. Depends on the
    display server (gap G24, ADR 0016 § 1) and must be reported, not assumed."""
    brightness_control: bool
    touch: bool


class DisplayPanel(Protocol):
    """No logical display state crosses this boundary — see the module docstring."""

    def set_power(self, on: bool) -> None: ...

    def set_brightness(self, level: int) -> None:
        """Logical 0-100. Meaningless while powered off; callers do not rely on an
        adapter doing anything useful with it in that case."""
        ...

    def on_touch(self, listener: TouchListener) -> None:
        """Register the display service as the touch recipient.

        Touch is delivered here, never to the UI directly: the service must be able
        to consume a wake touch before anything beneath the finger sees it
        (ADR 0016 § 3, `DISPLAY_STATE_MACHINE.md` invariant 7)."""
        ...

    def capabilities(self) -> PanelCapabilities: ...
