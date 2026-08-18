"""Qt event source for the fake-hardware desktop loop."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QKeyEvent

_KEY_NAMES = {
    Qt.Key.Key_Up: "up",
    Qt.Key.Key_Down: "down",
    Qt.Key.Key_Left: "left",
    Qt.Key.Key_Right: "right",
    Qt.Key.Key_Space: "space",
    Qt.Key.Key_W: "w",
    Qt.Key.Key_N: "n",
    Qt.Key.Key_A: "a",
    Qt.Key.Key_D: "d",
    Qt.Key.Key_S: "s",
    Qt.Key.Key_B: "b",
    Qt.Key.Key_0: "0",
    Qt.Key.Key_1: "1",
    Qt.Key.Key_2: "2",
    Qt.Key.Key_3: "3",
    Qt.Key.Key_4: "4",
    Qt.Key.Key_5: "5",
    Qt.Key.Key_6: "6",
    Qt.Key.Key_7: "7",
    Qt.Key.Key_8: "8",
    Qt.Key.Key_9: "9",
}


class QtDesktopInputSource(QObject):
    """Forward desktop keys and panel-like pointer presses to AQENO inputs."""

    def __init__(
        self,
        *,
        handle_key: Callable[[str], bool],
        handle_touch: Callable[[], bool],
        parent: QObject,
    ) -> None:
        super().__init__(parent)
        self._handle_key = handle_key
        self._handle_touch = handle_touch

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        if event.type() is QEvent.Type.MouseButtonPress:
            # Consume only a wake touch. Once interactive, the same event must
            # continue to QML so a visible tile can actually be selected.
            return self._handle_touch()
        if event.type() is not QEvent.Type.KeyPress:
            return False
        key_name = _KEY_NAMES.get(event.key()) if isinstance(event, QKeyEvent) else None
        return key_name is not None and self._handle_key(key_name)
