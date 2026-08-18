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
from aqeno.ports.audio import TransportState
from aqeno.ports.input import Back, FocusNext, FocusPrevious, InputEvent, Select
from aqeno.ports.persistence import ContentQuery, Library


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
    focused_content_id: ContentId | None = None
    """Which tile a navigation press would activate (ADR 0024). Only Home offers
    a choice, so this is `None` on every other surface and on an empty library."""


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
        self._surface = DeviceSurface(self._display_snapshot.wake_target)
        self._focus_index = 0
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
            focused = self._focused_id()
            self._tiles = tiles
            # A scan must not move the selection out from under a person's hand:
            # keep focus on the same content while it is still there.
            self._focus_index = next(
                (index for index, tile in enumerate(tiles) if tile.content_id == focused), 0
            )
            self._notify_changed()

    # -- navigation (ADR 0024) ----------------------------------------------

    def handle_navigation(self, event: InputEvent) -> None:
        """Registered with `DisplayService.on_navigation`, never with the raw bus.

        The display owns the wake decision, so an input that only woke a dark
        panel never arrives here (`DISPLAY_STATE_MACHINE.md` note 15).
        """
        if isinstance(event, FocusPrevious):
            self._move_focus(-1)
        elif isinstance(event, FocusNext):
            self._move_focus(1)
        elif isinstance(event, Select):
            self.activate_focus()
        elif isinstance(event, Back):
            self.show_home()

    def activate_focus(self) -> bool:
        """Start the focused tile, exactly as tapping it would."""
        with self._lock:
            focused = self._focused_id()
        if focused is None:
            return False
        return self.select_content(focused)

    def _move_focus(self, step: int) -> None:
        with self._lock:
            # Only Home offers a choice. An endless encoder wraps rather than
            # hitting an invisible wall — easier to explain, and there is no
            # end of the list to discover in the dark.
            if self._surface is not DeviceSurface.HOME or not self._tiles:
                return
            self._focus_index = (self._focus_index + step) % len(self._tiles)
            self._notify_changed()

    def _focused_id(self) -> ContentId | None:
        if self._surface is not DeviceSurface.HOME or not self._tiles:
            return None
        index = min(self._focus_index, len(self._tiles) - 1)
        return self._tiles[index].content_id

    def select_content(self, content_id: ContentId) -> bool:
        """Start an available tile immediately; stale or unavailable IDs are ignored."""
        item = self._library.get_content(content_id)
        if (
            item is None
            or not item.available
            or not self._library.can_profile_access(content_id, self._profile.name)
        ):
            return False
        with self._lock:
            self._surface = DeviceSurface.NOW_PLAYING
        self._playback.start(item, self._profile)
        return True

    def show_home(self) -> None:
        """Return from playback context to the shallow Kids Early library."""
        with self._lock:
            if self._surface is DeviceSurface.HOME:
                return
            self._surface = DeviceSurface.HOME
            self._notify_changed()

    def _playback_changed(self, snapshot: PlaybackSnapshot) -> None:
        with self._lock:
            self._playback_snapshot = snapshot
            if snapshot.content_id is None or (
                snapshot.transport is TransportState.STOPPED and snapshot.failure_code is None
            ):
                self._surface = DeviceSurface.HOME
            self._notify_changed()

    def _display_changed(self, snapshot: DisplaySnapshot) -> None:
        with self._lock:
            entering_interactive = (
                self._display_snapshot.state.value != "interactive"
                and snapshot.state.value == "interactive"
            )
            self._display_snapshot = snapshot
            if entering_interactive:
                self._surface = DeviceSurface(snapshot.wake_target)
            self._notify_changed()

    def _read_tiles(self) -> tuple[LibraryTile, ...]:
        return tuple(
            LibraryTile(content_id=item.id, title=item.title, artwork=item.artwork)
            for item in self._library.query_content(
                ContentQuery(limit=100, available=True, profile_name=self._profile.name)
            ).items
            if item.available
        )

    def _snapshot(self) -> DeviceUiSnapshot:
        return DeviceUiSnapshot(
            surface=self._surface,
            tiles=self._tiles,
            playback=self._playback_snapshot,
            display=self._display_snapshot,
            focused_content_id=self._focused_id(),
        )

    def _notify_changed(self) -> None:
        snapshot = self._snapshot()
        for listener in tuple(self._listeners):
            listener(snapshot)
