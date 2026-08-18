from __future__ import annotations

import hashlib
import threading
import uuid
from datetime import timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from aqeno.adapters.fakes import FakeClock
from aqeno.adapters.fakes.input import FakeInputBus
from aqeno.adapters.fakes.persistence import FakeLibrary, FakeSettingsStore
from aqeno.adapters.local_assets import LocalAssetStore
from aqeno.application.management import (
    IngestionManagement,
    LibraryManagement,
    OperationRegistry,
    OperationState,
    TokenAssignment,
)
from aqeno.config.defaults import default_settings
from aqeno.domain.content import ContentId, ContentItem, ContentKind, Fingerprint, LocalFileSource
from aqeno.management.api import ManagementContext, create_app
from aqeno.ports.input import NfcPresented
from aqeno.ports.media_probe import ProbedFile

KEY = "test-management-key"
HEADERS = {"X-AQENO-Management-Key": KEY}


class UploadedFileProbe:
    def probe(self, path: Path) -> ProbedFile | None:
        data = path.read_bytes()
        stat = path.stat()
        return ProbedFile(
            path=path,
            size_bytes=stat.st_size,
            mtime=stat.st_mtime,
            fingerprint=Fingerprint(
                size_bytes=stat.st_size, digest=hashlib.blake2b(data, digest_size=16).digest()
            ),
            duration=timedelta(minutes=3),
            title=path.stem,
        )


def _item(title: str) -> ContentItem:
    return ContentItem(
        id=ContentId(),
        title=title,
        kind=ContentKind.AUDIOBOOK,
        sources=(LocalFileSource(Path(f"/media/{title}.mp3")),),
        duration=timedelta(minutes=10),
    )


class ApiFixture:
    def __init__(self, tmp_path: Path) -> None:
        self.library = FakeLibrary()
        self.settings_store = FakeSettingsStore()
        self.inputs = FakeInputBus()
        self.operations = OperationRegistry()
        self.assets = LocalAssetStore(
            media_root=tmp_path / "media", artwork_root=tmp_path / "artwork"
        )
        self.assets.media_root.mkdir(parents=True)
        self.context = ManagementContext(
            library=self.library,
            settings_store=self.settings_store,
            library_management=LibraryManagement(self.library),
            ingestion=IngestionManagement(
                library=self.library,
                probe=UploadedFileProbe(),
                clock=FakeClock(),
                operations=self.operations,
                artwork_dir=self.assets.artwork_root,
            ),
            operations=self.operations,
            tokens=TokenAssignment(self.library, self.inputs),
            assets=self.assets,
            management_key=KEY,
            device_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            data_dir=tmp_path,
        )
        self.client = TestClient(create_app(self.context))


def test_every_management_resource_requires_the_device_key(tmp_path: Path) -> None:
    api = ApiFixture(tmp_path)
    response = api.client.get("/api/v1/device")
    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "management_auth_required",
            "message": "A valid management key is required.",
            "details": None,
        }
    }
    assert api.client.get("/api/v1/device", headers=HEADERS).status_code == 200


def test_library_uses_bounded_stable_cursor_pagination_and_server_filters(tmp_path: Path) -> None:
    api = ApiFixture(tmp_path)
    for title in ("Gamma", "alpha", "Beta", "Alpine"):
        api.library.save_content(_item(title))

    first = api.client.get(
        "/api/v1/library/media", params={"limit": 2, "search": "a"}, headers=HEADERS
    )
    assert first.status_code == 200
    body = first.json()
    assert [item["title"] for item in body["items"]] == ["alpha", "Alpine"]
    assert body["total"] == 4
    assert body["next_cursor"]

    second = api.client.get(
        "/api/v1/library/media",
        params={"limit": 2, "search": "a", "cursor": body["next_cursor"]},
        headers=HEADERS,
    )
    assert [item["title"] for item in second.json()["items"]] == ["Beta", "Gamma"]
    assert second.json()["next_cursor"] is None


def test_media_metadata_and_artwork_mutate_the_one_library(tmp_path: Path) -> None:
    api = ApiFixture(tmp_path)
    item = _item("Old")
    api.library.save_content(item)

    changed = api.client.patch(
        f"/api/v1/library/media/{item.id.value}",
        json={"title": "New", "kind": "audio_drama", "language": "de"},
        headers=HEADERS,
    )
    assert changed.status_code == 200
    assert api.library.get_content(item.id).title == "New"  # type: ignore[union-attr]

    artwork = api.client.put(
        f"/api/v1/library/media/{item.id.value}/artwork",
        files={"file": ("cover.png", b"png-data", "image/png")},
        headers=HEADERS,
    )
    assert artwork.status_code == 200
    assert artwork.json()["artwork_url"].endswith("/artwork")
    assert api.client.get(artwork.json()["artwork_url"], headers=HEADERS).content == b"png-data"


def test_upload_import_is_an_operation_and_creates_a_media_object(tmp_path: Path) -> None:
    api = ApiFixture(tmp_path)
    completed = threading.Event()
    api.operations.on_changed(
        lambda operation: completed.set() if operation.state is OperationState.COMPLETED else None
    )

    response = api.client.post(
        "/api/v1/imports",
        files={"file": ("Story.mp3", b"fake-audio", "audio/mpeg")},
        headers=HEADERS,
    )
    assert response.status_code == 202
    assert completed.wait(timeout=2)
    operation = api.client.get(
        f"/api/v1/operations/{response.json()['id']}", headers=HEADERS
    ).json()
    assert operation["state"] == "completed"
    assert [item.title for item in api.library.list_content()] == ["Story"]


def test_token_capture_assignment_is_immediate_and_survives_browser_close(tmp_path: Path) -> None:
    api = ApiFixture(tmp_path)
    item = _item("Story")
    api.library.save_content(item)

    started = api.client.post("/api/v1/token-captures", headers=HEADERS)
    capture_id = started.json()["id"]
    api.inputs.emit(NfcPresented("04-A1-B2-C3"))
    detected = api.client.get(f"/api/v1/token-captures/{capture_id}", headers=HEADERS)
    assert detected.json()["state"] == "detected"

    assigned = api.client.put(
        f"/api/v1/token-captures/{capture_id}/assignment",
        json={"media_id": str(item.id.value)},
        headers=HEADERS,
    )
    assert assigned.status_code == 200
    assert api.library.resolve_tag("04-A1-B2-C3") == item.id


def test_settings_are_product_schemas_and_persist_atomically_through_store(tmp_path: Path) -> None:
    api = ApiFixture(tmp_path)
    current = api.client.get("/api/v1/settings", headers=HEADERS).json()
    current["volume"]["child_maximum"] = 60
    saved = api.client.put("/api/v1/settings", json=current, headers=HEADERS)
    assert saved.status_code == 200
    assert api.settings_store.load().volume.child_maximum == 60
    assert saved.json()["apply_mode"] == "restart_required"


def test_openapi_is_the_complete_client_boundary_and_excludes_future_cloud(tmp_path: Path) -> None:
    api = ApiFixture(tmp_path)
    schema = api.client.get("/api/openapi.json").json()
    paths = schema["paths"]
    assert "/api/v1/imports" in paths
    assert "/api/v1/token-captures/{capture_id}/assignment" in paths
    assert "/api/v1/library/media" in paths
    assert "/api/v1/settings" in paths
    assert "/api/v1/content-access/bulk" in paths
    assert "/api/v1/collections/{collection_id}/audience" in paths
    assert "/api/v1/profiles/{name}/favorites/{media_id}" in paths
    assert all("cloud" not in path and "message" not in path for path in paths)
    operation_schema = schema["components"]["schemas"]["OperationResponse"]
    assert "state" in operation_schema["properties"]


def test_management_failure_does_not_change_library_or_playback_contract(tmp_path: Path) -> None:
    api = ApiFixture(tmp_path)
    item = _item("Still here")
    api.library.save_content(item)
    response = api.client.patch(
        f"/api/v1/library/media/{uuid.uuid4()}", json={"title": "No"}, headers=HEADERS
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "media_not_found"
    assert api.library.get_content(item.id) == item
    assert api.client.get("/api/v1/playback", headers=HEADERS).json()["state"] == "not_reported"


def test_defaults_round_trip_without_hidden_configuration_loss(tmp_path: Path) -> None:
    api = ApiFixture(tmp_path)
    resource = api.client.get("/api/v1/settings", headers=HEADERS).json()
    assert api.client.put("/api/v1/settings", json=resource, headers=HEADERS).status_code == 200
    assert api.settings_store.load() == default_settings()
