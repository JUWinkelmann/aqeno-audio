"""Recording fake `DisplayPanel` — makes the state machine's invariants assertable
without hardware: tests read `calls` to check the exact ordered sequence of power
and brightness applications, which is what "no brightness call in between" (the
dark-room scenario) and "no flash on entering OFF" (invariant 5) actually mean.
"""

from __future__ import annotations

from aqeno.ports.display import PanelCapabilities, TouchListener


class FakeDisplayPanel:
    """`authoritative_off` is configurable so the degraded case — a panel that can
    only zero its backlight — is testable (ADR 0016 § 1)."""

    def __init__(
        self,
        *,
        authoritative_off: bool = True,
        brightness_control: bool = True,
        touch: bool = True,
    ) -> None:
        self._capabilities = PanelCapabilities(
            authoritative_off=authoritative_off,
            brightness_control=brightness_control,
            touch=touch,
        )
        self.calls: list[tuple[str, bool | int]] = []
        self.power_on = False
        self.brightness: int | None = None
        self._touch_listener: TouchListener | None = None

    def set_power(self, on: bool) -> None:
        self.power_on = on
        self.calls.append(("power", on))

    def set_brightness(self, level: int) -> None:
        self.brightness = level
        self.calls.append(("brightness", level))

    def on_touch(self, listener: TouchListener) -> None:
        self._touch_listener = listener

    def capabilities(self) -> PanelCapabilities:
        return self._capabilities

    def simulate_touch(self) -> None:
        """Test-only: the panel reports a physical touch. Not part of `DisplayPanel`."""
        if self._touch_listener is not None:
            self._touch_listener()
