"""Typed in-process state channel for the first Device UI vertical slice.

This is application state, not a Qt view model. ADR 0012's concrete Qt
properties and thread marshalling belong in ``ui/models`` once the QML contract
exists. Keeping this value framework-free lets the local core remain headless.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum, auto
from pathlib import Path

from aqeno.application.display import DisplayService, DisplaySnapshot
from aqeno.application.playback import PlaybackSession, PlaybackSnapshot
from aqeno.domain.content import ContentId
from aqeno.domain.profile import Profile
from aqeno.ports.persistence import Library


class DeviceSurface(StrEnum):
    HOME = auto()
    NOW_PLAYING = auto()


@dataclass(frozen=True, slots=True)
class LibraryTile:
    content_id: ContentId
    title: str
    artwork: Path | None


@dataclass(frozen=True, slots=True)
class DeviceUiSnapshot:
    surface: DeviceSurface
    tiles: tuple[LibraryTile, ...]
    playback: PlaybackSnapshot
    display: DisplaySnapshot


DeviceUiListener = Callable[[DeviceUiSnapshot], None]


class DeviceUiState:
    """Combines already-decided application state for an appliance presentation."""

    def __init__(
        self,
        *,
        library: Library,
        playback: PlaybackSession,
        display: DisplayService,
        profile: Profile,
    ) -> None:
        self._library = library
        self._playback = playback
        self._display = display
        self._profile = profile
        self._lock = threading.RLock()
        self._tiles = self._read_tiles()
        self._playback_snapshot = playback.snapshot
        self._display_snapshot = display.snapshot
        self._listeners: list[DeviceUiListener] = []

        playback.on_changed(self._playback_changed)
        display.on_changed(self._display_changed)

    @property
    def snapshot(self) -> DeviceUiSnapshot:
        with self._lock:
            return self._snapshot()

    def on_changed(self, listener: DeviceUiListener) -> None:
        """Register for future immutable snapshots; read ``snapshot`` initially.

        Delivery follows the source services and may occur on an audio callback
        or scan thread. ADR 0012 requires the future Qt view model to marshal it
        onto Qt's object thread.
        """
        with self._lock:
            self._listeners.append(listener)

    def refresh_library(self) -> None:
        """Refresh tiles after an explicit ingestion scan completes."""
        with self._lock:
            tiles = self._read_tiles()
            if tiles == self._tiles:
                return
            self._tiles = tiles
            self._notify_changed()

    def select_content(self, content_id: ContentId) -> bool:
        """Start an available tile immediately; stale or unavailable IDs are ignored."""
        item = self._library.get_content(content_id)
        if item is None or not item.available:
            return False
        self._playback.start(item, self._profile)
        return True

    def _playback_changed(self, snapshot: PlaybackSnapshot) -> None:
        with self._lock:
            self._playback_snapshot = snapshot
            self._notify_changed()

    def _display_changed(self, snapshot: DisplaySnapshot) -> None:
        with self._lock:
            self._display_snapshot = snapshot
            self._notify_changed()

    def _read_tiles(self) -> tuple[LibraryTile, ...]:
        return tuple(
            LibraryTile(content_id=item.id, title=item.title, artwork=item.artwork)
            for item in self._library.list_content()
            if item.available
        )

    def _snapshot(self) -> DeviceUiSnapshot:
        # Display policy already owns the Home/Now Playing decision. Reusing it
        # avoids a second definition drifting when a stopped session still has
        # an item for resume/history purposes.
        surface = DeviceSurface(self._display_snapshot.wake_target)
        return DeviceUiSnapshot(
            surface=surface,
            tiles=self._tiles,
            playback=self._playback_snapshot,
            display=self._display_snapshot,
        )

    def _notify_changed(self) -> None:
        snapshot = self._snapshot()
        for listener in tuple(self._listeners):
            listener(snapshot)
