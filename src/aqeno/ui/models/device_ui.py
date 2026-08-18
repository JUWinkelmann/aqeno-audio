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

from PySide6.QtCore import Property, QAbstractListModel, QModelIndex, QObject, Qt, Signal, Slot

from aqeno.application.device_ui import DeviceUiSnapshot, DeviceUiState, LibraryTile
from aqeno.domain.content import ContentId


def _artwork_url(tile: LibraryTile | None) -> str:
    if tile is None or tile.artwork is None:
        return ""
    return tile.artwork.resolve().as_uri()


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
            return _artwork_url(tile)
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


class DeviceUiModel(QObject):
    """Presentation-only Qt boundary over :class:`DeviceUiState`."""

    stateChanged = Signal()
    _snapshotReady = Signal()

    def __init__(self, state: DeviceUiState, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._state = state
        self._tiles = TileModel(self)
        self._snapshot = state.snapshot
        self._pending_snapshot: DeviceUiSnapshot | None = None
        self._snapshot_lock = threading.Lock()
        self._snapshotReady.connect(
            self._apply_pending_snapshot, Qt.ConnectionType.QueuedConnection
        )
        state.on_changed(self._snapshot_changed)
        self._tiles.replace(self._snapshot.tiles)

    @Property(QObject, constant=True)
    def tiles(self) -> TileModel:
        return self._tiles

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
        content_id = self._snapshot.playback.content_id
        tile = next(
            (candidate for candidate in self._snapshot.tiles if candidate.content_id == content_id),
            None,
        )
        return _artwork_url(tile)

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
        self.stateChanged.emit()
