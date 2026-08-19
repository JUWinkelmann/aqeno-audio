"""Qt view model for the bounded Kids Early Device UI slice.

The application state remains framework-free.  This module translates immutable
snapshots into Qt properties and deliberately marshals callbacks from playback
and ingestion threads onto the QObject thread (ADR 0012).
"""
# Qt's Python API uses these established mixed-case names for QML properties,
# signals, slots and QAbstractItemModel overrides.
# ruff: noqa: B008, N802, N815

from __future__ import annotations

import threading
import uuid
from collections.abc import Sequence
from datetime import timedelta
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QModelIndex,
    QObject,
    QSize,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QColor, QImageReader

from aqeno.application.device_ui import (
    DeviceUiSnapshot,
    DeviceUiState,
    LibrarySection,
    LibraryTile,
)
from aqeno.domain.content import ContentId


def _artwork_url(artwork: Path | None) -> str:
    if artwork is None:
        return ""
    return artwork.resolve().as_uri()


@lru_cache(maxsize=64)
def _ambient_tint(artwork: str) -> str:
    """The one colour a cover lends to the light around it.

    Computed once per artwork from a 12 x 12 decode, never from the displayed
    pixels every frame: the premium look comes from a cheap tinted halo, not
    from blurring the image live (brief, "visual fidelity through cheap
    primitives"). Returns an empty string when there is nothing to take.
    """
    reader = QImageReader(artwork)
    reader.setScaledSize(QSize(12, 12))
    image = reader.read()
    if image.isNull():
        return ""

    red = green = blue = weight_total = 0.0
    for y in range(image.height()):
        for x in range(image.width()):
            pixel = image.pixelColor(x, y)
            # Colourful pixels lead: an average over a mostly dark cover would
            # otherwise return a grey that lights nothing.
            weight = 0.25 + pixel.saturationF() * pixel.valueF() * 3.0
            red += pixel.redF() * weight
            green += pixel.greenF() * weight
            blue += pixel.blueF() * weight
            weight_total += weight
    if weight_total <= 0:
        return ""

    average = QColor.fromRgbF(red / weight_total, green / weight_total, blue / weight_total)
    hue = average.hueF()
    if hue < 0:
        hue = 0.0
    # Held at a constant, restrained lightness so a dark cover and a bright one
    # produce the same *amount* of light, only a different colour.
    tint = QColor.fromHsvF(hue, min(0.68, average.saturationF() * 1.5), 0.92)
    return str(tint.name())


def _ambient_color(artwork: Path | None) -> str:
    if artwork is None:
        return ""
    return _ambient_tint(str(artwork.resolve()))


def _clock_text(value: timedelta | None) -> str:
    """`m:ss`, or `h:mm:ss` for a long work. Never a bare second count."""
    if value is None:
        return ""
    total = max(0, int(value.total_seconds()))
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


class TileModel(QAbstractListModel):
    """Only the fields needed by the Kids Early image-tile delegate."""

    ContentIdRole = Qt.ItemDataRole.UserRole + 1
    TitleRole = Qt.ItemDataRole.UserRole + 2
    ArtworkRole = Qt.ItemDataRole.UserRole + 3

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tiles: tuple[LibraryTile, ...] = ()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._tiles)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        if not index.isValid() or not 0 <= index.row() < len(self._tiles):
            return None
        tile = self._tiles[index.row()]
        if role == self.ContentIdRole:
            return str(tile.content_id.value)
        if role == self.TitleRole:
            return tile.title
        if role == self.ArtworkRole:
            return _artwork_url(tile.artwork)
        return None

    def roleNames(self) -> dict[int, bytes]:
        return {
            self.ContentIdRole: b"contentId",
            self.TitleRole: b"title",
            self.ArtworkRole: b"artworkUrl",
        }

    def replace(self, tiles: Sequence[LibraryTile]) -> None:
        replacement = tuple(tiles)
        if replacement == self._tiles:
            return
        self.beginResetModel()
        self._tiles = replacement
        self.endResetModel()


class SectionModel(QAbstractListModel):
    """Home's areas. The label is chosen by the presentation from the stable key,
    so a translation never reaches into application state."""

    KeyRole = Qt.ItemDataRole.UserRole + 1
    CountRole = Qt.ItemDataRole.UserRole + 2
    ArtworkRole = Qt.ItemDataRole.UserRole + 3

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._sections: tuple[LibrarySection, ...] = ()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._sections)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        if not index.isValid() or not 0 <= index.row() < len(self._sections):
            return None
        section = self._sections[index.row()]
        if role == self.KeyRole:
            return section.key
        if role == self.CountRole:
            return section.count
        if role == self.ArtworkRole:
            return _artwork_url(section.artwork)
        return None

    def roleNames(self) -> dict[int, bytes]:
        return {
            self.KeyRole: b"sectionKey",
            self.CountRole: b"itemCount",
            self.ArtworkRole: b"artworkUrl",
        }

    def replace(self, sections: Sequence[LibrarySection]) -> None:
        replacement = tuple(sections)
        if replacement == self._sections:
            return
        self.beginResetModel()
        self._sections = replacement
        self.endResetModel()


class DeviceUiModel(QObject):
    """Presentation-only Qt boundary over :class:`DeviceUiState`."""

    stateChanged = Signal()
    unassignedTag = Signal()
    """A presented token resolved to nothing. Transient by nature, so it is a
    signal rather than snapshot state — and the presentation may only
    acknowledge it while the panel is already lit."""
    _snapshotReady = Signal()
    _unassignedTagReady = Signal()

    def __init__(self, state: DeviceUiState, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._state = state
        self._tiles = TileModel(self)
        self._sections = SectionModel(self)
        self._snapshot = state.snapshot
        self._pending_snapshot: DeviceUiSnapshot | None = None
        self._snapshot_lock = threading.Lock()
        self._snapshotReady.connect(
            self._apply_pending_snapshot, Qt.ConnectionType.QueuedConnection
        )
        self._unassignedTagReady.connect(self.unassignedTag, Qt.ConnectionType.QueuedConnection)
        state.on_changed(self._snapshot_changed)
        state.on_unassigned_tag(self._unassignedTagReady.emit)
        self._tiles.replace(self._snapshot.tiles)
        self._sections.replace(self._snapshot.sections)

    @Property(QObject, constant=True)
    def tiles(self) -> TileModel:
        return self._tiles

    @Property(QObject, constant=True)
    def sections(self) -> SectionModel:
        return self._sections

    @Property(str, notify=stateChanged)
    def focusedSectionKey(self) -> str:
        return self._snapshot.focused_section_key

    @Property(str, notify=stateChanged)
    def openSectionKey(self) -> str:
        return self._snapshot.open_section_key

    @Property(str, notify=stateChanged)
    def presentationLevel(self) -> str:
        """`visual`, `visual_label` or `informative` — density only, never
        capability (`DEVICE_UI_PRINCIPLES.md` § Presentation levels)."""
        return self._snapshot.presentation_level.value

    @Property(int, notify=stateChanged)
    def focusedSectionIndex(self) -> int:
        return next(
            (
                index
                for index, section in enumerate(self._snapshot.sections)
                if section.key == self._snapshot.focused_section_key
            ),
            0,
        )

    @Property(int, notify=stateChanged)
    def focusedSectionCount(self) -> int:
        return next(
            (
                section.count
                for section in self._snapshot.sections
                if section.key == self._snapshot.focused_section_key
            ),
            0,
        )

    @Property(int, notify=stateChanged)
    def itemCount(self) -> int:
        return len(self._snapshot.tiles)

    @Property(int, notify=stateChanged)
    def focusedIndex(self) -> int:
        """1-based position of the focused item, for a `3 / 18` style hint."""
        focused = self._snapshot.focused_content_id
        if focused is None:
            return 0
        return next(
            (
                index + 1
                for index, tile in enumerate(self._snapshot.tiles)
                if tile.content_id == focused
            ),
            0,
        )

    @Property(str, notify=stateChanged)
    def focusedTitle(self) -> str:
        focused = self._snapshot.focused_content_id
        return next(
            (tile.title for tile in self._snapshot.tiles if tile.content_id == focused),
            "",
        )

    @Property(int, notify=stateChanged)
    def volume(self) -> int:
        return self._snapshot.playback.volume

    @Property(str, notify=stateChanged)
    def positionText(self) -> str:
        return _clock_text(self._snapshot.playback.position)

    @Property(str, notify=stateChanged)
    def durationText(self) -> str:
        return _clock_text(self._snapshot.playback.duration)

    @Property(str, notify=stateChanged)
    def failureCode(self) -> str:
        """A stable code, never a message: the presentation owns the words
        (`FAILURE_STATES.md`)."""
        code = self._snapshot.playback.failure_code
        return code.value if code is not None else ""

    @Property(str, notify=stateChanged)
    def surface(self) -> str:
        return self._snapshot.surface.value

    @Property(str, notify=stateChanged)
    def displayState(self) -> str:
        return self._snapshot.display.state.value

    @Property(str, notify=stateChanged)
    def nowPlayingTitle(self) -> str:
        return self._snapshot.playback.title or ""

    @Property(str, notify=stateChanged)
    def nowPlayingChapter(self) -> str:
        return self._snapshot.playback.chapter_title or ""

    @Property(str, notify=stateChanged)
    def nowPlayingArtworkUrl(self) -> str:
        return _artwork_url(self._snapshot.now_playing_artwork)

    @Property(str, notify=stateChanged)
    def nowPlayingAmbientColor(self) -> str:
        """The dominant colour of the current cover, for the light around it.
        Empty when there is no artwork, so the presentation can stay dark
        rather than invent a colour."""
        return _ambient_color(self._snapshot.now_playing_artwork)

    @Property(str, notify=stateChanged)
    def focusedContentId(self) -> str:
        """Which tile physical navigation would activate (ADR 0024)."""
        focused = self._snapshot.focused_content_id
        return str(focused.value) if focused is not None else ""

    @Property(str, notify=stateChanged)
    def nowPlayingContentId(self) -> str:
        content_id = self._snapshot.playback.content_id
        return str(content_id.value) if content_id is not None else ""

    @Property(float, notify=stateChanged)
    def progress(self) -> float:
        position = self._snapshot.playback.position
        duration = self._snapshot.playback.duration
        if position is None or duration is None or duration.total_seconds() <= 0:
            return 0.0
        return max(0.0, min(position / duration, 1.0))

    @Property(bool, notify=stateChanged)
    def hasPlaybackFailure(self) -> bool:
        return self._snapshot.playback.failure_code is not None

    @Property(bool, notify=stateChanged)
    def libraryEmpty(self) -> bool:
        return not self._snapshot.sections

    @Property(bool, notify=stateChanged)
    def playing(self) -> bool:
        return self._snapshot.playback.transport.value == "playing"

    @Slot(str)
    def selectContent(self, content_id: str) -> None:
        try:
            parsed = ContentId(uuid.UUID(content_id))
        except (ValueError, AttributeError):
            return
        self._state.select_content(parsed)

    @Slot(str)
    def openSection(self, key: str) -> None:
        self._state.open_section(key)

    @Slot()
    def showHome(self) -> None:
        self._state.show_home()

    def _snapshot_changed(self, snapshot: DeviceUiSnapshot) -> None:
        # Source callbacks may be audio or scan threads.  Signal delivery is
        # queued to this QObject's thread; QML never observes a foreign thread.
        with self._snapshot_lock:
            self._pending_snapshot = snapshot
        self._snapshotReady.emit()

    @Slot()
    def _apply_pending_snapshot(self) -> None:
        with self._snapshot_lock:
            snapshot = self._pending_snapshot
            self._pending_snapshot = None
        if snapshot is None:
            return
        self._snapshot = snapshot
        self._tiles.replace(snapshot.tiles)
        self._sections.replace(snapshot.sections)
        self.stateChanged.emit()
