from __future__ import annotations

import threading
import uuid
from pathlib import Path

from PySide6.QtCore import QCoreApplication

from aqeno.application.device_ui import DeviceSurface, DeviceUiSnapshot, LibraryTile
from aqeno.application.display import DisplaySnapshot
from aqeno.application.playback import PlaybackSnapshot
from aqeno.domain.content import ContentId
from aqeno.domain.display import DisplayState
from aqeno.ports.audio import TransportState
from aqeno.ui.models.device_ui import DeviceUiModel, TileModel


class _State:
    def __init__(self, snapshot: DeviceUiSnapshot) -> None:
        self.snapshot = snapshot
        self._listeners = []
        self.selected: ContentId | None = None

    def on_changed(self, listener) -> None:
        self._listeners.append(listener)

    def emit(self, snapshot: DeviceUiSnapshot) -> None:
        self.snapshot = snapshot
        for listener in self._listeners:
            listener(snapshot)

    def select_content(self, content_id: ContentId) -> bool:
        self.selected = content_id
        return True


def _snapshot(title: str = "") -> DeviceUiSnapshot:
    content_id = ContentId(uuid.uuid4())
    tile = LibraryTile(content_id, title, Path("/tmp/cover.jpg"))
    return DeviceUiSnapshot(
        surface=DeviceSurface.NOW_PLAYING if title else DeviceSurface.HOME,
        tiles=(tile,),
        playback=PlaybackSnapshot(
            transport=TransportState.PLAYING if title else TransportState.STOPPED,
            content_id=content_id if title else None,
            title=title or None,
            chapter_title=None,
            position=None,
            duration=None,
            volume=50,
            failure_code=None,
            can_toggle_playback=bool(title),
            can_skip_forward=False,
            can_skip_back=False,
        ),
        display=DisplaySnapshot(
            state=DisplayState.DIM if title else DisplayState.INTERACTIVE,
            wake_target="now_playing" if title else "home",
        ),
    )


def _app() -> QCoreApplication:
    return QCoreApplication.instance() or QCoreApplication([])


def test_tile_model_exposes_only_its_small_presentation_contract() -> None:
    model = TileModel()
    snapshot = _snapshot()
    model.replace(snapshot.tiles)

    index = model.index(0, 0)
    roles = model.roleNames()
    assert model.rowCount() == 1
    assert model.data(index, next(key for key, value in roles.items() if value == b"title")) == ""


def test_snapshot_callbacks_are_applied_on_qt_thread() -> None:
    _app()
    state = _State(_snapshot())
    model = DeviceUiModel(state)  # type: ignore[arg-type]
    received: list[str] = []
    model.stateChanged.connect(lambda: received.append(model.nowPlayingTitle))

    worker = threading.Thread(target=lambda: state.emit(_snapshot("Story")))
    worker.start()
    worker.join()
    assert model.nowPlayingTitle == ""

    QCoreApplication.processEvents()

    assert received == ["Story"]
    assert model.displayState == "dim"


def test_off_surface_cannot_receive_the_touch_that_wakes_the_panel() -> None:
    # Panel touch is consumed by DisplayService before a visible QML surface is
    # restored.  The declarative gate is the presentation-side half of ADR 0016:
    # while OFF, no child (and therefore no TapHandler) is hit-testable.
    qml = Path("src/aqeno/ui/qml/Main.qml").read_text()
    assert 'visible: deviceUi.displayState !== "off"' in qml
    assert 'visible: deviceUi.displayState === "interactive" && deviceUi.surface === "home"' in qml


def test_ui_runtime_marks_readiness_without_automatically_waking_display(monkeypatch) -> None:
    from aqeno.ui import runtime

    class App:
        @staticmethod
        def instance():
            return None

        def __init__(self, argv) -> None:
            pass

    class Root:
        def __init__(self) -> None:
            self.visible = False

        def setProperty(self, name: str, value: object) -> None:  # noqa: N802
            assert name == "visible"
            self.visible = bool(value)

    class Context:
        def setContextProperty(self, name: str, value: object) -> None:  # noqa: N802
            assert name == "deviceUi"

    class Engine:
        def __init__(self) -> None:
            self.root = Root()

        def rootContext(self) -> Context:  # noqa: N802
            return Context()

        def load(self, url: object) -> None:
            pass

        def rootObjects(self) -> list[Root]:  # noqa: N802
            return [self.root]

    class Readiness:
        def __init__(self) -> None:
            self.current = 2
            self.advanced = []

        def has_reached(self, state: object) -> bool:
            return False

        def advance(self, state: object) -> None:
            self.advanced.append(state)

    class Process:
        device_ui = object()
        readiness = Readiness()

    monkeypatch.setattr(runtime, "QGuiApplication", App)
    monkeypatch.setattr(runtime, "QQmlApplicationEngine", Engine)
    monkeypatch.setattr(runtime, "DeviceUiModel", lambda state: object())

    ui = runtime.DeviceUiRuntime(Process())  # type: ignore[arg-type]

    assert Process.readiness.advanced == [runtime.ReadinessState.UI_READY]
    assert ui._engine.root.visible is True
