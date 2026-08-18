from __future__ import annotations

import threading
from io import BytesIO
from pathlib import Path

import pytest

from aqeno.adapters.fakes.input import FakeInputBus
from aqeno.adapters.fakes.persistence import FakeLibrary
from aqeno.adapters.local_assets import LocalAssetStore, UploadTooLargeError
from aqeno.application.management import (
    OperationRegistry,
    OperationType,
    TokenAssignment,
    TokenCaptureState,
    TokenNotDetectedError,
)
from aqeno.domain.content import ContentId
from aqeno.ports.input import NfcPresented


def test_failed_media_upload_removes_temporary_file_and_empty_import_directory(
    tmp_path: Path,
) -> None:
    assets = LocalAssetStore(media_root=tmp_path / "media", artwork_root=tmp_path / "artwork")
    with pytest.raises(UploadTooLargeError):
        assets.store_media(BytesIO(b"too large"), filename="story.mp3", maximum_bytes=2)

    imports = tmp_path / "media" / "imports"
    assert not imports.exists() or list(imports.iterdir()) == []


def test_new_capture_cancels_previous_and_cancelled_capture_cannot_be_assigned() -> None:
    inputs = FakeInputBus()
    assignments = TokenAssignment(FakeLibrary(), inputs)
    first = assignments.start_capture()
    inputs.emit(NfcPresented("first-token"))

    second = assignments.start_capture()

    assert assignments.get_capture(first.id).state is TokenCaptureState.CANCELLED
    assert assignments.get_capture(second.id).state is TokenCaptureState.WAITING
    with pytest.raises(TokenNotDetectedError):
        assignments.assign(first.id, ContentId())


def test_operation_registry_waits_for_running_work_before_shutdown() -> None:
    registry = OperationRegistry()
    started = threading.Event()
    release = threading.Event()
    closed = threading.Event()

    def work() -> dict[str, object]:
        started.set()
        release.wait(timeout=2)
        return {}

    registry.submit(OperationType.LIBRARY_SCAN, work)
    assert started.wait(timeout=1)
    thread = threading.Thread(target=lambda: (registry.close(), closed.set()))
    thread.start()
    assert not closed.wait(timeout=0.05)
    release.set()
    thread.join(timeout=1)
    assert closed.is_set()
    with pytest.raises(RuntimeError):
        registry.submit(OperationType.LIBRARY_SCAN, lambda: {})
