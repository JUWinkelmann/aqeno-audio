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
from PySide6.QtGui import QColor, QGuiApplication, QLinearGradient, QPainter, QPixmap
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

VIEWPORTS = {"rh1": (800, 480), "small": (480, 320)}

VARIANTS: tuple[tuple[str, str, str, dict[str, object]], ...] = (
    # name, screen, presentation level, per-variant properties
    ("Clock", "ClockScreen", "informative", {}),
    ("TimerSetup", "TimerSetupScreen", "informative", {}),
    ("TimerRunning", "TimerRunningScreen", "informative", {}),
    ("TimerFinished", "TimerFinishedScreen", "informative", {}),
    ("AlarmRinging", "AlarmRingingScreen", "informative", {}),
    ("MessageAvailable", "MessageAvailableScreen", "informative", {}),
    ("MessagePlaying", "MessagePlayingScreen", "informative", {}),
    ("ContextActions", "ContextActionsScreen", "informative", {}),
    # Presentation levels change density only, never what a surface can do.
    # `visual` is the honest pre-reader test: what survives with no text at all.
    ("Clock-visual", "ClockScreen", "visual", {}),
    ("TimerRunning-visual", "TimerRunningScreen", "visual", {}),
    ("TimerFinished-visual", "TimerFinishedScreen", "visual", {}),
    ("AlarmRinging-visual", "AlarmRingingScreen", "visual", {}),
    ("MessageAvailable-visual", "MessageAvailableScreen", "visual", {}),
    # With portrait material the person becomes the mark rather than the name.
    ("MessageAvailable-portrait", "MessageAvailableScreen", "visual", {}),
    ("MessagePlaying-portrait", "MessagePlayingScreen", "informative", {}),
)

PORTRAIT_VARIANTS = frozenset({"MessageAvailable-portrait", "MessagePlaying-portrait"})

PREVIEW_DIR = Path(__file__).resolve().parent / "ui_preview"


def _settle(milliseconds: int) -> None:
    """Let bindings, layout and Canvas paints finish before grabbing."""
    timer = QElapsedTimer()
    timer.start()
    while timer.elapsed() < milliseconds:
        QCoreApplication.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 20)


def _portrait(path: Path) -> Path:
    """A neutral stand-in for sender material AQENO does not have.

    Deliberately abstract: it shows the *hierarchy* a portrait would create and
    claims nothing about a portrait system existing.
    """
    pixmap = QPixmap(400, 400)
    gradient = QLinearGradient(0, 0, 400, 400)
    gradient.setColorAt(0.0, QColor("#3d4f63"))
    gradient.setColorAt(1.0, QColor("#22303f"))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.fillRect(0, 0, 400, 400, gradient)
    painter.setBrush(QColor(255, 255, 255, 48))
    painter.setPen(QColor(0, 0, 0, 0))
    painter.drawEllipse(150, 96, 100, 100)
    painter.drawEllipse(96, 226, 208, 200)
    painter.end()
    pixmap.save(str(path), "PNG")
    return path


def _render(
    screen: str, size: tuple[int, int], out: Path, level: str, props: dict[str, object]
) -> None:
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("previewScreen", screen)
    engine.rootContext().setContextProperty("previewLevel", level)
    engine.rootContext().setContextProperty("previewProperties", props)
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
    args.out.mkdir(parents=True, exist_ok=True)
    portrait = _portrait(args.out / "_sender.png")
    for viewport, size in VIEWPORTS.items():
        for name, screen, level, props in VARIANTS:
            variant = dict(props)
            if name in PORTRAIT_VARIANTS:
                variant["senderPortrait"] = portrait.resolve().as_uri()
            _render(screen, size, args.out / viewport / f"{name}.png", level, variant)
        print(f"rendered {viewport} ({size[0]}x{size[1]}), {len(VARIANTS)} states")
    print(f"design targets in {args.out} — not product surfaces, see ui_preview/README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
