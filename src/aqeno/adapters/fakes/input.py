from __future__ import annotations

from aqeno.ports.input import InputEvent, InputListener


class FakeInputBus:
    def __init__(self) -> None:
        self._listeners: list[InputListener] = []

    def on_input(self, listener: InputListener) -> None:
        self._listeners.append(listener)

    def emit(self, event: InputEvent) -> None:
        for listener in tuple(self._listeners):
            listener(event)
