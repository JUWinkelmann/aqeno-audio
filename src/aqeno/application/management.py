"""Local management use cases, independent of HTTP and FastAPI (ADR 0018)."""

from __future__ import annotations

import threading
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from enum import StrEnum, auto
from pathlib import Path
from typing import Any

from aqeno.application.ingestion import ScanSummary, run_scan
from aqeno.config.defaults import Settings
from aqeno.domain.access import AccessDecision, Audience, Collection, CollectionId, EffectiveAccess
from aqeno.domain.content import ContentId, ContentItem, ContentKind
from aqeno.domain.profile import DisplayPolicy, ExperienceLevel, Profile, Role, VolumeLimits
from aqeno.ports.clock import Clock
from aqeno.ports.input import InputBus, InputEvent, NfcPresented
from aqeno.ports.media_probe import MediaProbe
from aqeno.ports.persistence import ContentPage, ContentQuery, Library, SettingsStore


class ManagementError(Exception):
    code = "management_error"


class ContentNotFoundError(ManagementError):
    code = "media_not_found"


class TokenCaptureNotFoundError(ManagementError):
    code = "token_capture_not_found"


class TokenNotDetectedError(ManagementError):
    code = "token_not_detected"


class ProfileNotFoundError(ManagementError):
    code = "profile_not_found"


class CollectionNotFoundError(ManagementError):
    code = "collection_not_found"


class BulkLimitError(ManagementError):
    code = "bulk_limit_exceeded"


class OperationType(StrEnum):
    MEDIA_IMPORT = auto()
    LIBRARY_SCAN = auto()


class OperationState(StrEnum):
    QUEUED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()


@dataclass(frozen=True, slots=True)
class Operation:
    id: uuid.UUID
    type: OperationType
    state: OperationState
    progress: int
    result: dict[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None


OperationListener = Callable[[Operation], None]


class OperationRegistry:
    """Small process-local runner for scan/import work; not a generic job queue."""

    def __init__(self) -> None:
        self._operations: dict[uuid.UUID, Operation] = {}
        self._listeners: list[OperationListener] = []
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="aqeno-management")

    def on_changed(self, listener: OperationListener) -> None:
        with self._lock:
            self._listeners.append(listener)

    def list(self) -> tuple[Operation, ...]:
        with self._lock:
            return tuple(self._operations.values())

    def get(self, operation_id: uuid.UUID) -> Operation | None:
        with self._lock:
            return self._operations.get(operation_id)

    def submit(self, kind: OperationType, work: Callable[[], dict[str, Any]]) -> Operation:
        operation = Operation(id=uuid.uuid4(), type=kind, state=OperationState.QUEUED, progress=0)
        self._set(operation)
        self._executor.submit(self._run, operation, work)
        return operation

    def close(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=False)

    def _run(self, operation: Operation, work: Callable[[], dict[str, Any]]) -> None:
        current = replace(operation, state=OperationState.RUNNING, progress=5)
        self._set(current)
        try:
            result = work()
        except Exception as exc:
            self._set(
                replace(
                    current,
                    state=OperationState.FAILED,
                    progress=100,
                    error_code="operation_failed",
                    error_message=str(exc),
                )
            )
        else:
            self._set(
                replace(
                    current,
                    state=OperationState.COMPLETED,
                    progress=100,
                    result=result,
                )
            )

    def _set(self, operation: Operation) -> None:
        with self._lock:
            self._operations[operation.id] = operation
            listeners = tuple(self._listeners)
        for listener in listeners:
            listener(operation)


class LibraryManagement:
    def __init__(self, library: Library) -> None:
        self._library = library

    def query(self, query: ContentQuery) -> ContentPage:
        return self._library.query_content(query)

    def get(self, content_id: ContentId) -> ContentItem:
        item = self._library.get_content(content_id)
        if item is None:
            raise ContentNotFoundError(str(content_id.value))
        return item

    def update_metadata(
        self,
        content_id: ContentId,
        *,
        title: str | None = None,
        kind: ContentKind | None = None,
        language: str | None = None,
    ) -> ContentItem:
        item = self.get(content_id)
        updated = replace(
            item,
            title=title if title is not None else item.title,
            kind=kind if kind is not None else item.kind,
            language=language if language is not None else item.language,
            kind_overridden=item.kind_overridden or kind is not None,
        )
        self._library.save_content(updated)
        return updated

    def set_artwork(self, content_id: ContentId, path: Path | None) -> ContentItem:
        updated = replace(self.get(content_id), artwork=path)
        self._library.save_content(updated)
        return updated

    def remove(self, content_id: ContentId) -> None:
        self.get(content_id)
        self._library.remove_content(content_id)


class IngestionManagement:
    def __init__(
        self,
        *,
        library: Library,
        probe: MediaProbe,
        clock: Clock,
        operations: OperationRegistry,
        artwork_dir: Path,
    ) -> None:
        self._library = library
        self._probe = probe
        self._clock = clock
        self._operations = operations
        self._artwork_dir = artwork_dir

    def scan(self, roots: tuple[Path, ...], *, imported: bool = False) -> Operation:
        def work() -> dict[str, Any]:
            summary: ScanSummary = run_scan(
                library=self._library,
                probe=self._probe,
                clock=self._clock,
                roots=roots,
                follow_symlinks=False,
                artwork_dir=self._artwork_dir,
            )
            return {
                "candidates_seen": summary.candidates_seen,
                "works_touched": summary.works_touched,
                "works_marked_unavailable": summary.works_marked_unavailable,
            }

        return self._operations.submit(
            OperationType.MEDIA_IMPORT if imported else OperationType.LIBRARY_SCAN, work
        )


class TokenCaptureState(StrEnum):
    WAITING = auto()
    DETECTED = auto()
    ASSIGNED = auto()


@dataclass(frozen=True, slots=True)
class TokenCapture:
    id: uuid.UUID
    state: TokenCaptureState
    token_uid: str | None = None
    content_id: ContentId | None = None


TokenListener = Callable[[TokenCapture], None]


class TokenAssignment:
    def __init__(self, library: Library, input_bus: InputBus) -> None:
        self._library = library
        self._captures: dict[uuid.UUID, TokenCapture] = {}
        self._active: uuid.UUID | None = None
        self._listeners: list[TokenListener] = []
        self._lock = threading.RLock()
        input_bus.on_input(self._handle_input)

    def on_changed(self, listener: TokenListener) -> None:
        with self._lock:
            self._listeners.append(listener)

    def start_capture(self) -> TokenCapture:
        capture = TokenCapture(id=uuid.uuid4(), state=TokenCaptureState.WAITING)
        with self._lock:
            self._captures[capture.id] = capture
            self._active = capture.id
        self._notify(capture)
        return capture

    def get_capture(self, capture_id: uuid.UUID) -> TokenCapture:
        with self._lock:
            capture = self._captures.get(capture_id)
        if capture is None:
            raise TokenCaptureNotFoundError(str(capture_id))
        return capture

    def assign(self, capture_id: uuid.UUID, content_id: ContentId) -> TokenCapture:
        capture = self.get_capture(capture_id)
        if capture.token_uid is None:
            raise TokenNotDetectedError(str(capture_id))
        if self._library.get_content(content_id) is None:
            raise ContentNotFoundError(str(content_id.value))
        self._library.map_tag(capture.token_uid, content_id)
        assigned = replace(capture, state=TokenCaptureState.ASSIGNED, content_id=content_id)
        with self._lock:
            self._captures[capture_id] = assigned
            if self._active == capture_id:
                self._active = None
        self._notify(assigned)
        return assigned

    def _handle_input(self, event: InputEvent) -> None:
        if not isinstance(event, NfcPresented):
            return
        with self._lock:
            if self._active is None:
                return
            capture = self._captures[self._active]
            detected = replace(capture, state=TokenCaptureState.DETECTED, token_uid=event.tag_id)
            self._captures[capture.id] = detected
        self._notify(detected)

    def _notify(self, capture: TokenCapture) -> None:
        with self._lock:
            listeners = tuple(self._listeners)
        for listener in listeners:
            listener(capture)


class ConfigurationManagement:
    def __init__(self, library: Library, settings_store: SettingsStore) -> None:
        self._library = library
        self._settings_store = settings_store

    def settings(self) -> Settings:
        return self._settings_store.load()

    def save_settings(self, settings: Settings) -> Settings:
        self._settings_store.save(settings)
        return settings

    def profiles(self) -> tuple[Profile, ...]:
        return self._library.list_profiles()

    def profile(self, name: str) -> Profile | None:
        return self._library.get_profile(name)

    def save_profile(
        self,
        *,
        name: str,
        level: ExperienceLevel,
        role: Role,
        display: DisplayPolicy,
        volume: VolumeLimits,
        ambient_enabled: bool,
    ) -> Profile:
        profile = Profile(
            name=name,
            level=level,
            role=role,
            display=display,
            volume=volume,
            ambient_enabled=ambient_enabled,
        )
        self._library.save_profile(profile)
        return profile

    def remove_profile(self, name: str) -> None:
        if self._library.get_profile(name) is None:
            raise ProfileNotFoundError(name)
        self._library.remove_profile(name)


class ProfileContentManagement:
    MAX_MEDIA_PER_MUTATION = 1000
    MAX_PROFILES_PER_MUTATION = 50

    def __init__(self, library: Library) -> None:
        self._library = library

    def set_audience(self, content_ids: tuple[ContentId, ...], audience: Audience) -> None:
        self._validate(content_ids, audience.profile_names)
        self._library.set_content_audience(content_ids, audience)

    def set_overrides(
        self,
        content_ids: tuple[ContentId, ...],
        profile_names: tuple[str, ...],
        decision: AccessDecision | None,
    ) -> None:
        self._validate(content_ids, profile_names)
        self._library.set_content_overrides(content_ids, profile_names, decision)

    def effective(self, content_id: ContentId, profile_name: str) -> EffectiveAccess:
        self._require_content(content_id)
        self._require_profiles((profile_name,))
        return self._library.effective_access(content_id, profile_name)

    def set_favorite(self, profile_name: str, content_id: ContentId, favorite: bool) -> None:
        self._require_content(content_id)
        self._require_profiles((profile_name,))
        self._library.set_favorite(profile_name, content_id, favorite)

    def save_collection(self, collection: Collection) -> None:
        if len(collection.content_ids) > self.MAX_MEDIA_PER_MUTATION:
            raise BulkLimitError(str(len(collection.content_ids)))
        for content_id in collection.content_ids:
            self._require_content(content_id)
        self._library.save_collection(collection)

    def set_collection_audience(self, collection_id: CollectionId, audience: Audience) -> None:
        if self._library.get_collection(collection_id) is None:
            raise CollectionNotFoundError(str(collection_id.value))
        self._require_profiles(audience.profile_names)
        self._library.set_collection_audience(collection_id, audience)

    def remove_collection(self, collection_id: CollectionId) -> None:
        if self._library.get_collection(collection_id) is None:
            raise CollectionNotFoundError(str(collection_id.value))
        self._library.remove_collection(collection_id)

    def _validate(self, content_ids: tuple[ContentId, ...], profile_names: tuple[str, ...]) -> None:
        if (
            len(content_ids) > self.MAX_MEDIA_PER_MUTATION
            or len(profile_names) > self.MAX_PROFILES_PER_MUTATION
        ):
            raise BulkLimitError(
                f"maximum {self.MAX_MEDIA_PER_MUTATION} media and "
                f"{self.MAX_PROFILES_PER_MUTATION} profiles"
            )
        for content_id in content_ids:
            self._require_content(content_id)
        self._require_profiles(profile_names)

    def _require_content(self, content_id: ContentId) -> None:
        if self._library.get_content(content_id) is None:
            raise ContentNotFoundError(str(content_id.value))

    def _require_profiles(self, profile_names: tuple[str, ...]) -> None:
        for profile_name in profile_names:
            if self._library.get_profile(profile_name) is None:
                raise ProfileNotFoundError(profile_name)
