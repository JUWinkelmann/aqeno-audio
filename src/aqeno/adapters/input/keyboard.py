"""Desktop keyboard input used by the fake-hardware development loop."""

from __future__ import annotations

from collections.abc import Callable

from aqeno.ports.input import (
    FocusNext,
    FocusPrevious,
    Home,
    InputEvent,
    InputListener,
    Next,
    NfcPresented,
    NfcRemoved,
    Previous,
    Select,
    TogglePlayback,
    VolumeDelta,
    WakeRequest,
)

_FIXED_TEST_UIDS = {str(number): f"AQENO-TEST-{number}" for number in range(1, 10)}


class KeyboardSimulator:
    """Turns normalized key names from the future UI shell into semantic input."""

    def __init__(self, *, toggle_night: Callable[[], None] | None = None) -> None:
        self._listeners: list[InputListener] = []
        self._toggle_night = toggle_night
        self._presented_tag: str | None = None

    def on_input(self, listener: InputListener) -> None:
        self._listeners.append(listener)

    def handle_key(self, key: str) -> bool:
        """Handle a key from `DEVELOPMENT.md`; return whether it was recognized."""
        normalized = key.casefold()
        event: InputEvent | None = None

        if normalized == "up":
            event = VolumeDelta(1)
        elif normalized == "down":
            event = VolumeDelta(-1)
        elif normalized == "space":
            event = TogglePlayback()
        elif normalized == "right":
            event = Next()
        elif normalized == "left":
            event = Previous()
        elif normalized == "w":
            event = WakeRequest()
        # Navigation (ADR 0024, ADR 0026): the desktop stand-in for the SELECT
        # encoder and the HOME key, so the touch-free journey is exercised on
        # every run and not only in tests.
        elif normalized == "a":
            event = FocusPrevious()
        elif normalized == "d":
            event = FocusNext()
        elif normalized == "s":
            event = Select()
        elif normalized == "h":
            event = Home()
        elif normalized in _FIXED_TEST_UIDS:
            self._presented_tag = _FIXED_TEST_UIDS[normalized]
            event = NfcPresented(self._presented_tag)
        elif normalized == "0":
            if self._presented_tag is None:
                return True
            event = NfcRemoved(self._presented_tag)
            self._presented_tag = None
        elif normalized == "n":
            if self._toggle_night is not None:
                self._toggle_night()
            return True
        else:
            return False

        self._emit(event)
        return True

    def _emit(self, event: InputEvent) -> None:
        for listener in tuple(self._listeners):
            listener(event)
