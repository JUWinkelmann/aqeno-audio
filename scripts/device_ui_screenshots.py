"""Render the Device UI offscreen so its states can be reviewed by eye.

`AGENTS.md` asks for evidence rather than assertion: QML that compiles is not a
surface that reads well. This renders every implemented state at RH1's viewport
and at a smaller panel of roughly the class ADR 0025 § 1 prefers, so both can be
looked at before anything is claimed about them.

It is a development tool. It renders the real `Main.qml` with real application
state over a fake library — nothing here is a second implementation of the UI.

    python scripts/device_ui_screenshots.py --out build/ui
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from functools import partial
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QElapsedTimer, QEventLoop, QUrl
from PySide6.QtGui import QColor, QGuiApplication, QLinearGradient, QPainter, QPixmap
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from aqeno.adapters.fakes import (
    FakeAudioEngine,
    FakeClock,
    FakeDisplayPanel,
    FakeInputBus,
    FakeLibrary,
    FakeStatusLeds,
)
from aqeno.application.device_ui import DeviceUiState
from aqeno.application.display import DisplayService
from aqeno.application.playback import PlaybackSession
from aqeno.application.readiness import Readiness, ReadinessState
from aqeno.config.defaults import default_settings
from aqeno.domain.content import ContentId, ContentItem, ContentKind, HttpSource
from aqeno.domain.display import DisplayEvent
from aqeno.domain.profile import (
    DisplayPolicy,
    ExperienceLevel,
    Profile,
    Role,
    VolumeLimits,
)
from aqeno.ui.models.device_ui import DeviceUiModel

VIEWPORTS = {"rh1": (800, 480), "small": (480, 320)}
"""RH1's real panel, and a smaller one of the preferred later class. The point
is that the hierarchy survives both, not that either is a product decision."""

DEMO = (
    ("Der Wal und die Möwe", ContentKind.AUDIO_DRAMA, "#2f6f6b", "#123a3c"),
    ("Nachts im Hafen", ContentKind.AUDIO_DRAMA, "#4a3f72", "#1d1a33"),
    ("Sieben Steine", ContentKind.AUDIO_DRAMA, "#6d4030", "#2a1a14"),
    ("Das lange Tal", ContentKind.AUDIOBOOK, "#38506e", "#161f2c"),
    ("Wolkenlieder", ContentKind.MUSIC_ALBUM, "#6b4a63", "#281c26"),
    ("Nordwelle", ContentKind.RADIO_STREAM, "#2c5a45", "#12241c"),
)


def _artwork(path: Path, top: str, bottom: str, title: str) -> Path:
    """Neutral AQENO-authored placeholders — no third-party artwork is used."""
    pixmap = QPixmap(600, 600)
    gradient = QLinearGradient(0, 0, 600, 600)
    gradient.setColorAt(0.0, QColor(top))
    gradient.setColorAt(1.0, QColor(bottom))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.fillRect(0, 0, 600, 600, gradient)
    painter.setPen(QColor(255, 255, 255, 38))
    for index in range(3):
        painter.drawEllipse(160 + index * 70, 150 + index * 40, 300, 300)
    painter.end()
    pixmap.save(str(path), "PNG")
    return path


def _profile() -> Profile:
    return Profile(
        name="kids-early",
        level=ExperienceLevel.KIDS_EARLY,
        role=Role.USER,
        display=DisplayPolicy(
            inactivity_timeout=timedelta(seconds=30),
            night_timeout=timedelta(seconds=10),
            allows_dim=True,
            dim_hold=timedelta(seconds=10),
            interactive_brightness=70,
            dim_brightness=8,
            ambient_brightness=40,
            night_brightness=5,
            led_brightness=20,
        ),
        volume=VolumeLimits(maximum=70, night_maximum=35, headphone_maximum=55),
    )


@dataclass
class Harness:
    state: DeviceUiState
    playback: PlaybackSession
    display: DisplayService
    library: FakeLibrary
    items: tuple[ContentItem, ...]
    profile: Profile


def _harness(art_dir: Path, *, empty: bool = False) -> Harness:
    clock = FakeClock()
    library = FakeLibrary()
    items: list[ContentItem] = []
    if not empty:
        for index, (title, kind, top, bottom) in enumerate(DEMO):
            cover = _artwork(art_dir / f"cover{index}.png", top, bottom, title)
            item = ContentItem(
                id=ContentId(),
                title=title,
                kind=kind,
                sources=(HttpSource(f"https://example.invalid/{index}", seekable=True),),
                duration=timedelta(minutes=27, seconds=10),
                artwork=cover,
            )
            library.save_content(item)
            items.append(item)

    playback = PlaybackSession(
        audio=FakeAudioEngine(),
        library=library,
        clock=clock,
        settings=default_settings(),
        inputs=FakeInputBus(),
    )
    profile = _profile()
    playback.use_profile(profile)
    readiness = Readiness(clock)
    for rung in (
        ReadinessState.LOCAL_READY,
        ReadinessState.PLAYBACK_READY,
        ReadinessState.UI_READY,
    ):
        readiness.advance(rung)
    display = DisplayService(
        panel=FakeDisplayPanel(),
        leds=FakeStatusLeds(),
        clock=clock,
        readiness=readiness,
        profile=profile,
        settings=default_settings(),
    )
    playback.on_changed(display.handle_playback_changed)
    display.handle_event(DisplayEvent.WAKE_REQUEST)
    state = DeviceUiState(library=library, playback=playback, display=display, profile=profile)
    display.on_navigation(state.handle_navigation)
    playback.on_tag_unassigned(state.note_unassigned_tag)
    state.refresh_library()
    return Harness(
        state=state,
        playback=playback,
        display=display,
        library=library,
        items=tuple(items),
        profile=profile,
    )


def _settle(milliseconds: int) -> None:
    """Let bindings, layout and asynchronous artwork finish before grabbing.

    A grab taken in the same tick as the resize captures the previous layout,
    which is exactly the kind of screenshot that would lie about the design.
    """
    timer = QElapsedTimer()
    timer.start()
    while timer.elapsed() < milliseconds:
        QCoreApplication.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 20)


def _render(
    model: DeviceUiModel,
    size: tuple[int, int],
    out: Path,
    once_showing: Callable[[], None] | None = None,
) -> None:
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("deviceUi", model)
    qml = Path(__file__).resolve().parents[1] / "src/aqeno/ui/qml/Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml)))
    roots = engine.rootObjects()
    if not roots:
        raise SystemExit(f"QML failed to load: {qml}")
    window = roots[0]
    assert isinstance(window, QQuickWindow)
    window.setVisibility(QQuickWindow.Visibility.Windowed)
    window.setGeometry(0, 0, size[0], size[1])
    window.setVisible(True)
    _settle(200)
    if once_showing is not None:
        # A transient overlay reacts to a change it *observed*, so the change
        # has to happen with the surface already on screen.
        once_showing()
    _settle(400)
    image = window.grabWindow()
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(str(out), "PNG")
    window.setVisible(False)
    engine.deleteLater()
    _settle(30)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="build/ui", type=Path)
    args = parser.parse_args()

    QGuiApplication(sys.argv[:1])
    art_dir = args.out / "_artwork"
    art_dir.mkdir(parents=True, exist_ok=True)

    for viewport, size in VIEWPORTS.items():
        for name, prepare, after in _states():
            harness = _harness(art_dir, empty=name == "empty")
            prepare(harness)
            model = DeviceUiModel(harness.state)
            _render(
                model,
                size,
                args.out / viewport / f"{name}.png",
                once_showing=partial(after, harness),
            )
            model.deleteLater()
        print(f"rendered {viewport} ({size[0]}x{size[1]})")
    print(f"screenshots in {args.out}")
    return 0


def _states() -> tuple[tuple[str, object, object], ...]:
    def nothing(_: Harness) -> None:
        return None

    def home(_: Harness) -> None:
        return None

    def browse(harness: Harness) -> None:
        harness.state.open_section("audio_drama")

    def browse_second(harness: Harness) -> None:
        harness.state.open_section("audio_drama")
        from aqeno.ports.input import FocusNext

        harness.state.handle_navigation(FocusNext())

    def now_playing(harness: Harness) -> None:
        # Resume part-way through, so progress is actually reviewable. It goes
        # through the real resume path rather than being poked into the model.
        harness.library.set_resume(
            harness.items[0].id, harness.profile.name, timedelta(minutes=15, seconds=40)
        )
        harness.state.open_section("audio_drama")
        harness.state.select_content(harness.items[0].id)

    def paused(harness: Harness) -> None:
        now_playing(harness)
        harness.playback.toggle_playback()

    def turn_volume(harness: Harness) -> None:
        from aqeno.ports.input import VolumeDelta

        harness.playback.handle_input(VolumeDelta(-2))

    def present_unknown_tag(harness: Harness) -> None:
        harness.state.note_unassigned_tag()

    def dim(harness: Harness) -> None:
        now_playing(harness)
        harness.display.handle_event(DisplayEvent.INACTIVITY_ELAPSED)

    def off(harness: Harness) -> None:
        harness.display.set_night_active(True)

    def empty(_: Harness) -> None:
        return None

    return (
        ("home", home, nothing),
        ("browse", browse, nothing),
        ("browse-second", browse_second, nothing),
        ("now-playing", now_playing, nothing),
        ("paused", paused, nothing),
        ("volume", now_playing, turn_volume),
        ("notice", home, present_unknown_tag),
        ("dim", dim, nothing),
        ("off", off, nothing),
        ("empty", empty, nothing),
    )


if __name__ == "__main__":
    raise SystemExit(main())
