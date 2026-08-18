"""Explicitly unavailable physical input source."""

from __future__ import annotations

from aqeno.ports.input import ControlCapability, ControlInputListener


class UnavailablePhysicalInput:
    @property
    def controls(self) -> tuple[ControlCapability, ...]:
        return ()

    def on_control_input(self, listener: ControlInputListener) -> None:
        del listener

    def start(self) -> None:
        pass

    def close(self) -> None:
        pass
