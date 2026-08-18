"""Null display panel for first-class headless operation — ADR 0017."""

from __future__ import annotations

from aqeno.ports.display import PanelCapabilities, TouchListener


class NullDisplayPanel:
    """A physically absent panel is authoritatively dark by definition."""

    def set_power(self, on: bool) -> None:
        pass

    def set_brightness(self, level: int) -> None:
        pass

    def on_touch(self, listener: TouchListener) -> None:
        pass

    def capabilities(self) -> PanelCapabilities:
        return PanelCapabilities(
            authoritative_off=True,
            brightness_control=False,
            touch=False,
        )
