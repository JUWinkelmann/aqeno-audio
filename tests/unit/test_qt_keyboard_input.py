from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtGui import QKeyEvent

from aqeno.adapters.input.desktop_qt import QtDesktopInputSource


def _app() -> QCoreApplication:
    return QCoreApplication.instance() or QCoreApplication([])


def test_qt_key_press_reaches_normalized_keyboard_adapter() -> None:
    app = _app()
    received: list[str] = []
    source = QtDesktopInputSource(
        handle_key=lambda key: received.append(key) is None,
        handle_touch=lambda: False,
        parent=app,
    )

    handled = source.eventFilter(
        app,
        QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_W, Qt.KeyboardModifier.NoModifier),
    )

    assert handled
    assert received == ["w"]


def test_qt_keyboard_source_ignores_unmapped_and_release_events() -> None:
    app = _app()
    source = QtDesktopInputSource(
        handle_key=lambda key: True,
        handle_touch=lambda: False,
        parent=app,
    )

    assert not source.eventFilter(
        app,
        QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier),
    )
    assert not source.eventFilter(
        app,
        QKeyEvent(QEvent.Type.KeyRelease, Qt.Key.Key_W, Qt.KeyboardModifier.NoModifier),
    )


def test_desktop_pointer_press_consumes_only_a_wake_touch() -> None:
    app = _app()
    touches: list[bool] = []
    source = QtDesktopInputSource(
        handle_key=lambda key: True,
        handle_touch=lambda: touches.append(True) is None,
        parent=app,
    )

    handled = source.eventFilter(
        app,
        QEvent(QEvent.Type.MouseButtonPress),
    )

    assert handled
    assert touches == [True]

    interactive_source = QtDesktopInputSource(
        handle_key=lambda key: True,
        handle_touch=lambda: False,
        parent=app,
    )
    assert not interactive_source.eventFilter(
        app,
        QEvent(QEvent.Type.MouseButtonPress),
    )
