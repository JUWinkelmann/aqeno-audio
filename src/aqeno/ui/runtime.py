"""In-process Qt Quick runtime for the Device UI.

Importing this module is intentionally deferred by the composition root.  A
headless AQENO process therefore has no Qt startup or display dependency.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from PySide6.QtCore import QCoreApplication, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from aqeno.application.device_ui import DeviceUiState
from aqeno.application.readiness import Readiness, ReadinessState
from aqeno.ui.models.device_ui import DeviceUiModel


class DeviceUiProcess(Protocol):
    device_ui: DeviceUiState
    readiness: Readiness


class DeviceUiRuntime:
    """Owns the Qt application and QML engine for one AQENO process."""

    def __init__(self, process: DeviceUiProcess, argv: list[str] | None = None) -> None:
        # Avoid importing or constructing Qt from the headless composition path.
        self._process = process
        self._app = QGuiApplication.instance() or QGuiApplication(argv or [])
        self._engine = QQmlApplicationEngine()
        self._model = DeviceUiModel(process.device_ui)
        self._engine.rootContext().setContextProperty("deviceUi", self._model)
        qml_path = Path(__file__).with_name("qml") / "Main.qml"
        self._engine.load(QUrl.fromLocalFile(str(qml_path)))
        if not self._engine.rootObjects():
            raise RuntimeError(f"Device UI failed to load: {qml_path}")
        if not process.readiness.has_reached(ReadinessState.UI_READY):
            process.readiness.advance(ReadinessState.UI_READY)
        self._engine.rootObjects()[0].setProperty("visible", True)

    @property
    def app(self) -> QCoreApplication:
        return self._app

    def exec(self) -> int:
        return self._app.exec()

    def close(self) -> None:
        self._engine.deleteLater()
        self._model.deleteLater()


def start_device_ui(process: DeviceUiProcess) -> DeviceUiRuntime:
    """Load the QML surface, raising without changing Core readiness on failure."""
    return DeviceUiRuntime(process)
