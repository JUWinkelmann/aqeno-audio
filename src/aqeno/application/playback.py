"""The local playback session for the first vertical slice."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

from aqeno.config.defaults import Settings
from aqeno.domain.content import ContentId, ContentItem, Source, TransportBehaviour
from aqeno.domain.profile import Profile
from aqeno.ports.audio import AudioEngine, AudioFailure, FailureCode, TransportState
from aqeno.ports.clock import Clock
from aqeno.ports.input import (
    InputBus,
    InputEvent,
    Next,
    NfcPresented,
    Previous,
    TogglePlayback,
    VolumeDelta,
)
from aqeno.ports.persistence import Library

RESUME_PERSIST_INTERVAL = timedelta(seconds=10)
FINISHED_REMAINING = timedelta(seconds=30)
FINISHED_FRACTION = 0.98
MAX_VOLUME_JUMP = 5


@dataclass(frozen=True, slots=True)
class PlaybackSnapshot:
    """Application-owned state exposed to presentation adapters.

    Failure detail is deliberately absent: child-facing presentation may react to a stable code,
    while technical text remains available through `PlaybackSession.last_failure` for diagnosis.
    """

    transport: TransportState
    content_id: ContentId | None
    title: str | None
    chapter_title: str | None
    position: timedelta | None
    duration: timedelta | None
    volume: int
    failure_code: FailureCode | None
    can_toggle_playback: bool
    can_skip_forward: bool
    can_skip_back: bool


PlaybackListener = Callable[[PlaybackSnapshot], None]


class SourceResolutionRequiredError(ValueError):
    """An item has alternative Sources and no resolution decision exists yet."""


class PlaybackSession:
    """Coordinates one local item across audio, controls and resume persistence."""

    def __init__(
        self,
        *,
        audio: AudioEngine,
        library: Library,
        clock: Clock,
        settings: Settings,
        inputs: InputBus,
    ) -> None:
        self._audio = audio
        self._library = library
        self._clock = clock
        self._settings = settings
        self._lock = threading.RLock()

        self._item: ContentItem | None = None
        self._profile: Profile | None = None
        self._sources: tuple[Source, ...] = ()
        self._source_offsets: tuple[timedelta, ...] = ()
        self._source_index = 0
        self._resume_handle: object | None = None
        self._start_position = timedelta(0)
        self._starting = False
        self._resume_enabled = False
        self._night_active = False
        self._headphones = False
        self._volume = settings.volume.first_boot
        self._last_failure: AudioFailure | None = None
        self._listeners: list[PlaybackListener] = []

        audio.on_state(self._on_audio_state)
        audio.on_failure(self._on_audio_failure)
        audio.on_source_changed(self._on_source_changed)
        audio.on_finished(self._on_finished)
        inputs.on_input(self.handle_input)

    @property
    def item(self) -> ContentItem | None:
        return self._item

    @property
    def volume(self) -> int:
        return self._volume

    @property
    def last_failure(self) -> AudioFailure | None:
        return self._last_failure

    @property
    def snapshot(self) -> PlaybackSnapshot:
        with self._lock:
            item = self._item
            position = self._absolute_position() if item is not None else None
            can_skip_forward, can_skip_back = self._skip_availability(position)
            return PlaybackSnapshot(
                transport=self._audio.state,
                content_id=item.id if item is not None else None,
                title=item.title if item is not None else None,
                chapter_title=self._chapter_title(position),
                position=position,
                duration=item.duration if item is not None else None,
                volume=self._volume,
                failure_code=self._last_failure.code if self._last_failure is not None else None,
                can_toggle_playback=self._audio.state
                in (TransportState.PLAYING, TransportState.PAUSED),
                can_skip_forward=can_skip_forward,
                can_skip_back=can_skip_back,
            )

    def on_changed(self, listener: PlaybackListener) -> None:
        """Register for future snapshots; read `snapshot` once for initial state.

        Delivery is synchronous on the thread that changed playback. A Qt view model must marshal
        notifications from the audio callback thread onto Qt's object thread (ADR 0012).
        """
        with self._lock:
            self._listeners.append(listener)

    def start(self, item: ContentItem, profile: Profile) -> None:
        with self._lock:
            self._persist_position()
            sources, offsets = _playback_sources(item)
            saved = self._resume_for(item, profile)
            source_index = _source_at(offsets, saved)

            self._cancel_resume_checkpoint()
            self._item = item
            self._profile = profile
            self._sources = sources
            self._source_offsets = offsets
            self._source_index = source_index
            self._start_position = saved - offsets[source_index]
            self._starting = True
            self._resume_enabled = False
            self._last_failure = None
            self._apply_volume(self._volume)

            self._audio.load(sources[source_index])
            self._prepare_following_source()

    def use_profile(self, profile: Profile) -> None:
        with self._lock:
            if self._profile == profile:
                return
            self._persist_position()
            self._profile = profile
            self._apply_volume(self._volume)
            self._notify_changed()

    def toggle_playback(self) -> None:
        with self._lock:
            if self._audio.state is TransportState.PLAYING:
                self._persist_position()
                self._audio.pause()
            elif self._audio.state is TransportState.PAUSED:
                self._audio.play()

    def stop(self) -> None:
        with self._lock:
            self._persist_position()
            self._cancel_resume_checkpoint()
            self._audio.stop()

    def set_night_active(self, active: bool) -> None:
        with self._lock:
            self._night_active = active
            self._apply_volume(self._volume)
            self._notify_changed()

    def set_headphones(self, present: bool) -> None:
        with self._lock:
            self._headphones = present
            self._apply_volume(self._volume)
            self._notify_changed()

    def handle_input(self, event: InputEvent) -> None:
        if isinstance(event, VolumeDelta):
            with self._lock:
                requested = event.delta * self._settings.volume.encoder_step
                jump = max(-MAX_VOLUME_JUMP, min(requested, MAX_VOLUME_JUMP))
                self._apply_volume(self._volume + jump)
                self._notify_changed()
        elif isinstance(event, TogglePlayback):
            self.toggle_playback()
        elif isinstance(event, Next):
            self.next()
        elif isinstance(event, Previous):
            self.previous()
        elif isinstance(event, NfcPresented):
            self._launch_tag(event.tag_id)

    def next(self) -> None:
        with self._lock:
            item = self._item
            if item is None or item.policy.transport is TransportBehaviour.IGNORED:
                return
            if item.policy.transport is TransportBehaviour.CHAPTER_ELSE_SKIP:
                if item.has_chapters:
                    self._move_to_chapter(1)
                elif item.policy.skip_forward is not None:
                    self._seek_absolute(self._absolute_position() + item.policy.skip_forward)

    def previous(self) -> None:
        with self._lock:
            item = self._item
            if item is None or item.policy.transport is TransportBehaviour.IGNORED:
                return
            if item.policy.transport is TransportBehaviour.CHAPTER_ELSE_SKIP:
                if item.has_chapters:
                    self._move_to_chapter(-1)
                elif item.policy.skip_back is not None:
                    self._seek_absolute(self._absolute_position() - item.policy.skip_back)

    def shutdown(self) -> None:
        with self._lock:
            self._persist_position()
            self._cancel_resume_checkpoint()

    def _launch_tag(self, tag_id: str) -> None:
        with self._lock:
            profile = self._profile
            content_id = self._library.resolve_tag(tag_id)
            if profile is None or content_id is None:
                return
            item = self._library.get_content(content_id)
            if item is not None:
                self.start(item, profile)

    def _on_audio_state(self, state: TransportState) -> None:
        with self._lock:
            if state is TransportState.PAUSED and self._starting:
                self._starting = False
                capabilities = self._audio.capabilities
                self._resume_enabled = capabilities is not None and capabilities.seekable
                if capabilities is not None and capabilities.seekable:
                    self._audio.seek(self._start_position)
                self._audio.play()
                return
            elif state is TransportState.PLAYING:
                self._schedule_resume_checkpoint()
            elif state in (TransportState.PAUSED, TransportState.STOPPED, TransportState.FAILED):
                self._cancel_resume_checkpoint()
            self._notify_changed()

    def _on_audio_failure(self, failure: AudioFailure) -> None:
        with self._lock:
            self._persist_position()
            self._last_failure = failure
            self._starting = False

    def _on_source_changed(self, source: Source) -> None:
        with self._lock:
            try:
                self._source_index = self._sources.index(source)
            except ValueError:
                return
            capabilities = self._audio.capabilities
            self._resume_enabled = capabilities is not None and capabilities.seekable
            self._prepare_following_source()
            self._notify_changed()

    def _on_finished(self) -> None:
        with self._lock:
            self._cancel_resume_checkpoint()
            if self._resume_enabled and self._item is not None and self._profile is not None:
                duration = self._item.duration
                if duration is not None:
                    self._library.set_resume(self._item.id, self._profile.name, duration)

    def _prepare_following_source(self) -> None:
        following = self._source_index + 1
        source = self._sources[following] if following < len(self._sources) else None
        self._audio.prepare_next(source)

    def _resume_for(self, item: ContentItem, profile: Profile) -> timedelta:
        saved = self._library.get_resume(item.id, profile.name) or timedelta(0)
        duration = item.duration
        if duration is not None:
            saved = max(timedelta(0), min(saved, duration))
            if _is_finished(saved, duration):
                return timedelta(0)
        if not item.policy.exact_resume:
            minimum = item.policy.resume_minimum_duration
            if duration is None or minimum is None or duration < minimum:
                return timedelta(0)
        rewind = timedelta(seconds=self._settings.resume.rewind_seconds)
        return max(timedelta(0), saved - rewind)

    def _move_to_chapter(self, delta: int) -> None:
        assert self._item is not None
        chapters = self._item.chapters
        position = self._absolute_position()
        current = max(
            (index for index, chapter in enumerate(chapters) if chapter.start <= position),
            default=0,
        )
        target = max(0, min(current + delta, len(chapters) - 1))
        self._seek_absolute(chapters[target].start)

    def _seek_absolute(self, position: timedelta) -> None:
        item = self._item
        if item is None:
            return
        target = max(timedelta(0), position)
        if item.duration is not None:
            target = min(target, item.duration)
        source_index = _source_at(self._source_offsets, target)
        local_position = target - self._source_offsets[source_index]
        if source_index == self._source_index:
            self._audio.seek(local_position)
            self._notify_changed()
            return

        self._persist_position()
        self._cancel_resume_checkpoint()
        self._source_index = source_index
        self._start_position = local_position
        self._starting = True
        self._resume_enabled = False
        self._audio.load(self._sources[source_index])
        self._prepare_following_source()

    def _absolute_position(self) -> timedelta:
        position = self._audio.position or timedelta(0)
        if not self._source_offsets:
            return position
        return self._source_offsets[self._source_index] + position

    def _persist_position(self) -> None:
        if self._item is None or self._profile is None:
            return
        if not self._resume_enabled:
            return
        self._library.set_resume(self._item.id, self._profile.name, self._absolute_position())

    def _schedule_resume_checkpoint(self) -> None:
        if self._resume_handle is not None:
            return
        if not self._resume_enabled:
            return
        self._resume_handle = self._clock.schedule(RESUME_PERSIST_INTERVAL, self._resume_checkpoint)

    def _resume_checkpoint(self) -> None:
        with self._lock:
            self._resume_handle = None
            if self._audio.state is not TransportState.PLAYING:
                return
            self._persist_position()
            self._schedule_resume_checkpoint()

    def _cancel_resume_checkpoint(self) -> None:
        if self._resume_handle is None:
            return
        self._clock.cancel(self._resume_handle)
        self._resume_handle = None

    def _apply_volume(self, requested: int) -> None:
        profile = self._profile
        if profile is None:
            volume = max(0, min(requested, 100))
        else:
            volume = profile.volume.clamp(
                requested,
                night_active=self._night_active,
                headphones=self._headphones,
            )
        self._volume = volume
        self._audio.set_volume(volume)

    def _chapter_title(self, position: timedelta | None) -> str | None:
        item = self._item
        if item is None or position is None or not item.chapters:
            return None
        chapter = max(
            (chapter for chapter in item.chapters if chapter.start <= position),
            key=lambda chapter: chapter.start,
            default=None,
        )
        return chapter.title if chapter is not None else None

    def _skip_availability(self, position: timedelta | None) -> tuple[bool, bool]:
        item = self._item
        active = self._audio.state in (TransportState.PLAYING, TransportState.PAUSED)
        if (
            item is None
            or position is None
            or not active
            or item.policy.transport is not TransportBehaviour.CHAPTER_ELSE_SKIP
        ):
            return False, False
        if item.has_chapters:
            current = max(
                (index for index, chapter in enumerate(item.chapters) if chapter.start <= position),
                default=0,
            )
            return current < len(item.chapters) - 1, current > 0
        can_forward = item.policy.skip_forward is not None and (
            item.duration is None or position < item.duration
        )
        return can_forward, item.policy.skip_back is not None and position > timedelta(0)

    def _notify_changed(self) -> None:
        snapshot = self.snapshot
        for listener in tuple(self._listeners):
            listener(snapshot)


def _playback_sources(item: ContentItem) -> tuple[tuple[Source, ...], tuple[timedelta, ...]]:
    chapter_sources = tuple(chapter.source for chapter in item.chapters)
    if chapter_sources and all(source is not None for source in chapter_sources):
        return tuple(source for source in chapter_sources if source is not None), tuple(
            chapter.start for chapter in item.chapters
        )
    if len(item.sources) == 1:
        return item.sources, (timedelta(0),)
    raise SourceResolutionRequiredError(
        f"content {item.id.value} has {len(item.sources)} alternative sources; resolve one first"
    )


def _source_at(offsets: tuple[timedelta, ...], position: timedelta) -> int:
    return max((index for index, offset in enumerate(offsets) if offset <= position), default=0)


def _is_finished(position: timedelta, duration: timedelta) -> bool:
    if duration <= timedelta(0):
        return True
    return duration - position < FINISHED_REMAINING or position / duration >= FINISHED_FRACTION
