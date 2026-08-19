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
from aqeno.domain.content import ContentId, ContentKind
from aqeno.domain.profile import Profile
from aqeno.ports.audio import TransportState
from aqeno.ports.input import FocusNext, FocusPrevious, Home, InputEvent, Select
from aqeno.ports.persistence import ContentQuery, Library


class DeviceSurface(StrEnum):
    HOME = auto()
    """One dominant content area at a time; SELECT rotates between areas."""
    BROWSE = auto()
    """One dominant item inside the opened area."""
    NOW_PLAYING = auto()


@dataclass(frozen=True, slots=True)
class LibraryTile:
    content_id: ContentId
    title: str
    artwork: Path | None


@dataclass(frozen=True, slots=True)
class LibrarySection:
    """One Home area, derived from the content kinds ADR 0009 already defines.

    Areas are never invented: a section exists only while the library actually
    holds accessible items of its kinds, so an unavailable capability has no UI
    surface at all rather than an empty one (`PRODUCT_FOUNDATION.md` P15).
    """

    key: str
    kinds: tuple[ContentKind, ...]
    count: int
    artwork: Path | None


SECTION_KINDS: tuple[tuple[str, tuple[ContentKind, ...]], ...] = (
    ("audio_drama", (ContentKind.AUDIO_DRAMA,)),
    ("audiobook", (ContentKind.AUDIOBOOK,)),
    ("music", (ContentKind.MUSIC_ALBUM, ContentKind.MUSIC_TRACK)),
    ("podcast", (ContentKind.PODCAST_EPISODE,)),
    ("radio", (ContentKind.RADIO_STREAM,)),
    ("personal", (ContentKind.PERSONAL_RECORDING,)),
)
"""Home's taxonomy, in presentation order. It is the content model of
`PRODUCT_FOUNDATION.md` § 8 and ADR 0009 § 1 — not a new set of product areas."""


@dataclass(frozen=True, slots=True)
class DeviceUiSnapshot:
    surface: DeviceSurface
    tiles: tuple[LibraryTile, ...]
    """Items of the opened section, or the whole accessible library on Home."""
    playback: PlaybackSnapshot
    display: DisplaySnapshot
    sections: tuple[LibrarySection, ...] = ()
    focused_section_key: str = ""
    focused_content_id: ContentId | None = None
    """What a SELECT press would activate (ADR 0026). `None` wherever the
    surface offers no item choice, and on an empty library."""
    open_section_key: str = ""
    now_playing_artwork: Path | None = None
    """Resolved from the library rather than from `tiles`: what is playing may
    live in a section the person has since navigated away from."""


DeviceUiListener = Callable[[DeviceUiSnapshot], None]


class DeviceUiState:
    """Combines already-decided application state for an appliance presentation.

    The surface graph is deliberately three levels and no more:
    ``HOME -> BROWSE -> NOW_PLAYING``. HOME is reachable from every one of them
    through the physical HOME control, so no back stack exists (ADR 0026 § 4).
    """

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
        self._playback_snapshot = playback.snapshot
        self._display_snapshot = display.snapshot
        self._surface = DeviceSurface(self._display_snapshot.wake_target)
        self._sections: tuple[LibrarySection, ...] = ()
        self._section_index = 0
        self._open_section_key = ""
        self._tiles: tuple[LibraryTile, ...] = ()
        self._item_index = 0
        # Returning to a section should return to where the person was, not to
        # the top of a list they already scrolled through (§ State preservation).
        self._remembered_item_index: dict[str, int] = {}
        self._listeners: list[DeviceUiListener] = []
        self._unassigned_tag_listeners: list[Callable[[], None]] = []
        self._read_library()

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

    def on_unassigned_tag(self, listener: Callable[[], None]) -> None:
        """Transient notice that a presented token resolved to nothing.

        A transient event, not snapshot state: it has no duration and nothing
        persists it. The presentation may acknowledge it **only while the panel
        is already lit** — an unassigned token must never wake a dark display
        (`DISPLAY_STATE_MACHINE.md` note 7), and doing nothing at all remains
        the correct behaviour in the dark.
        """
        with self._lock:
            self._unassigned_tag_listeners.append(listener)

    def note_unassigned_tag(self) -> None:
        """Called by the playback session when a token resolves to nothing."""
        with self._lock:
            listeners = tuple(self._unassigned_tag_listeners)
        for listener in listeners:
            listener()

    def refresh_library(self) -> None:
        """Refresh sections and items after an explicit ingestion scan completes."""
        with self._lock:
            sections = self._sections
            focused = self._focused_id()
            self._read_library()
            if sections == self._sections and focused == self._focused_id():
                return
            # A scan must not move the selection out from under a person's hand:
            # keep focus on the same content while it is still there.
            if focused is not None:
                self._item_index = next(
                    (index for index, tile in enumerate(self._tiles) if tile.content_id == focused),
                    self._item_index,
                )
            self._clamp_focus()
            self._notify_changed()

    # -- navigation (ADR 0024, ADR 0026) -------------------------------------

    def handle_navigation(self, event: InputEvent) -> None:
        """Registered with `DisplayService.on_navigation`, never with the raw bus.

        The display owns the wake decision, so an input that only woke a dark
        panel never arrives here (`DISPLAY_STATE_MACHINE.md` note 15) — except
        `Home`, which is executed rather than consumed (note 17).
        """
        if isinstance(event, FocusPrevious):
            self._move_focus(-1)
        elif isinstance(event, FocusNext):
            self._move_focus(1)
        elif isinstance(event, Select):
            self.activate_focus()
        elif isinstance(event, Home):
            self.show_home()

    def activate_focus(self) -> bool:
        """SELECT press: open the focused section, or start the focused item."""
        with self._lock:
            surface = self._surface
            section = self._focused_section()
            focused = self._focused_id()
        if surface is DeviceSurface.HOME:
            return self.open_section(section.key) if section is not None else False
        if focused is None:
            return False
        return self.select_content(focused)

    def open_section(self, key: str) -> bool:
        """Enter a section's browse level, restoring where the person left it."""
        with self._lock:
            index = next(
                (position for position, item in enumerate(self._sections) if item.key == key), None
            )
            if index is None:
                return False
            self._section_index = index
            self._open_section_key = key
            self._surface = DeviceSurface.BROWSE
            self._tiles = self._read_tiles(self._sections[index].kinds)
            self._item_index = self._remembered_item_index.get(key, 0)
            self._clamp_focus()
            self._notify_changed()
        return True

    def _move_focus(self, step: int) -> None:
        with self._lock:
            # An endless encoder wraps rather than hitting an invisible wall —
            # easier to explain, and there is no end of the list to discover in
            # the dark. Now Playing offers no choice, so rotation does nothing.
            if self._surface is DeviceSurface.HOME:
                if not self._sections:
                    return
                self._section_index = (self._section_index + step) % len(self._sections)
            elif self._surface is DeviceSurface.BROWSE:
                if not self._tiles:
                    return
                self._item_index = (self._item_index + step) % len(self._tiles)
                self._remembered_item_index[self._open_section_key] = self._item_index
            else:
                return
            self._notify_changed()

    def _focused_section(self) -> LibrarySection | None:
        if not self._sections:
            return None
        return self._sections[min(self._section_index, len(self._sections) - 1)]

    def _focused_id(self) -> ContentId | None:
        if self._surface is not DeviceSurface.BROWSE or not self._tiles:
            return None
        return self._tiles[min(self._item_index, len(self._tiles) - 1)].content_id

    def _clamp_focus(self) -> None:
        self._section_index = (
            min(self._section_index, len(self._sections) - 1) if self._sections else 0
        )
        self._item_index = min(self._item_index, len(self._tiles) - 1) if self._tiles else 0

    def select_content(self, content_id: ContentId) -> bool:
        """Start an available item immediately; stale or unavailable IDs are ignored."""
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
        """The physical HOME control: always the same place, from anywhere."""
        with self._lock:
            if self._surface is DeviceSurface.HOME:
                return
            self._surface = DeviceSurface.HOME
            self._open_section_key = ""
            self._notify_changed()

    def _playback_changed(self, snapshot: PlaybackSnapshot) -> None:
        with self._lock:
            self._playback_snapshot = snapshot
            # Only Now Playing may be left because playback ended — it is the
            # surface that no longer has anything to show. A transport control
            # must never navigate (ADR 0026 § 3), so a Play/Pause or Next press
            # while browsing leaves the person exactly where they were.
            ended = snapshot.content_id is None or (
                snapshot.transport is TransportState.STOPPED and snapshot.failure_code is None
            )
            if ended and self._surface is DeviceSurface.NOW_PLAYING:
                self._surface = DeviceSurface.HOME
                self._open_section_key = ""
            self._notify_changed()

    def _display_changed(self, snapshot: DisplaySnapshot) -> None:
        with self._lock:
            entering_interactive = (
                self._display_snapshot.state.value != "interactive"
                and snapshot.state.value == "interactive"
            )
            self._display_snapshot = snapshot
            if entering_interactive:
                # Deterministic wake target: Now Playing during playback, else
                # Home. Never a half-remembered browse position nobody expects.
                self._surface = DeviceSurface(snapshot.wake_target)
                if self._surface is DeviceSurface.HOME:
                    self._open_section_key = ""
            self._notify_changed()

    def _read_library(self) -> None:
        """Recompute Home's sections, then the open section's items."""
        sections: list[LibrarySection] = []
        for key, kinds in SECTION_KINDS:
            items = self._read_tiles(kinds)
            if not items:
                continue
            artwork = next((tile.artwork for tile in items if tile.artwork is not None), None)
            sections.append(LibrarySection(key=key, kinds=kinds, count=len(items), artwork=artwork))
        self._sections = tuple(sections)
        open_section = next(
            (item for item in self._sections if item.key == self._open_section_key), None
        )
        if open_section is None:
            self._open_section_key = ""
            self._tiles = ()
            if self._surface is DeviceSurface.BROWSE:
                self._surface = DeviceSurface.HOME
        else:
            self._tiles = self._read_tiles(open_section.kinds)
        self._clamp_focus()

    def _read_tiles(self, kinds: tuple[ContentKind, ...]) -> tuple[LibraryTile, ...]:
        found: list[LibraryTile] = []
        for kind in kinds:
            found.extend(
                LibraryTile(content_id=item.id, title=item.title, artwork=item.artwork)
                for item in self._library.query_content(
                    ContentQuery(
                        limit=200,
                        kind=kind,
                        available=True,
                        profile_name=self._profile.name,
                    )
                ).items
                if item.available
            )
        return tuple(found)

    def _now_playing_artwork(self) -> Path | None:
        content_id = self._playback_snapshot.content_id
        if content_id is None:
            return None
        item = self._library.get_content(content_id)
        return item.artwork if item is not None else None

    def _snapshot(self) -> DeviceUiSnapshot:
        section = self._focused_section()
        return DeviceUiSnapshot(
            surface=self._surface,
            tiles=self._tiles,
            playback=self._playback_snapshot,
            display=self._display_snapshot,
            sections=self._sections,
            focused_section_key=section.key if section is not None else "",
            focused_content_id=self._focused_id(),
            open_section_key=self._open_section_key,
            now_playing_artwork=self._now_playing_artwork(),
        )

    def _notify_changed(self) -> None:
        snapshot = self._snapshot()
        for listener in tuple(self._listeners):
            listener(snapshot)
