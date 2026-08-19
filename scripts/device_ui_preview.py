"""Render the Device UI design targets — screens for capabilities AQENO lacks.

Separate from `device_ui_screenshots.py` on purpose. That script renders the
**real** surface driven by real application state; this one renders visual target
states for the clock, the visual timer, the alarm and personal messages, none of
which has domain behaviour yet.

Keeping them apart is what stops a design target from being mistaken for a
shipped screen. Nothing rendered here is reachable from the running Device UI:
an unavailable capability has no device surface (`PRODUCT_FOUNDATION.md` P15).

    python scripts/device_ui_preview.py --out build/ui-preview
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QElapsedTimer, QEventLoop, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

VIEWPORTS = {"rh1": (800, 480), "small": (480, 320)}

SCREENS = (
    "ClockScreen",
    "TimerSetupScreen",
    "TimerRunningScreen",
    "TimerFinishedScreen",
    "AlarmRingingScreen",
    "MessageAvailableScreen",
    "MessagePlayingScreen",
)

PREVIEW_DIR = Path(__file__).resolve().parent / "ui_preview"


def _settle(milliseconds: int) -> None:
    """Let bindings, layout and Canvas paints finish before grabbing."""
    timer = QElapsedTimer()
    timer.start()
    while timer.elapsed() < milliseconds:
        QCoreApplication.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 20)


def _render(screen: str, size: tuple[int, int], out: Path) -> None:
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("previewScreen", screen)
    engine.load(QUrl.fromLocalFile(str(PREVIEW_DIR / "PreviewHost.qml")))
    roots = engine.rootObjects()
    if not roots:
        raise SystemExit(f"preview failed to load: {screen}")
    window = roots[0]
    assert isinstance(window, QQuickWindow)
    window.setGeometry(0, 0, size[0], size[1])
    window.setVisible(True)
    _settle(300)
    out.parent.mkdir(parents=True, exist_ok=True)
    window.grabWindow().save(str(out), "PNG")
    window.setVisible(False)
    engine.deleteLater()
    _settle(30)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="build/ui-preview", type=Path)
    args = parser.parse_args()

    QGuiApplication(sys.argv[:1])
    for viewport, size in VIEWPORTS.items():
        for screen in SCREENS:
            name = screen.removesuffix("Screen")
            _render(screen, size, args.out / viewport / f"{name}.png")
        print(f"rendered {viewport} ({size[0]}x{size[1]})")
    print(f"design targets in {args.out} — not product surfaces, see ui_preview/README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
