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
from aqeno.application.control_mapping import MappedInputBus
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
from aqeno.management.auth import AdminAuth
from aqeno.ports.input import (
    ControlCapability,
    ControlEventType,
    ControlInput,
    ControlType,
    LogicalControl,
    Next,
    NfcPresented,
    Previous,
    TogglePlayback,
)
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


class PhysicalControls:
    def __init__(self) -> None:
        self._listeners = []

    @property
    def controls(self) -> tuple[ControlCapability, ...]:
        return (
            ControlCapability(
                LogicalControl.PRIMARY_LEFT,
                ControlType.BUTTON,
                "Linke Taste",
                (ControlEventType.SHORT_PRESS, ControlEventType.LONG_PRESS),
                True,
            ),
            ControlCapability(
                LogicalControl.PRIMARY_ENCODER,
                ControlType.ROTARY_ENCODER,
                "Drehknopf",
                (
                    ControlEventType.ROTATE_LEFT,
                    ControlEventType.ROTATE_RIGHT,
                    ControlEventType.SHORT_PRESS,
                    ControlEventType.LONG_PRESS,
                ),
                True,
            ),
            ControlCapability(
                LogicalControl.PRIMARY_RIGHT,
                ControlType.BUTTON,
                "Rechte Taste",
                (ControlEventType.SHORT_PRESS, ControlEventType.LONG_PRESS),
                True,
            ),
        )

    def on_control_input(self, listener: object) -> None:
        self._listeners.append(listener)

    def emit(self, event: ControlInput) -> None:
        for listener in tuple(self._listeners):
            assert callable(listener)
            listener(event)


def _item(title: str) -> ContentItem:
    return ContentItem(
        id=ContentId(),
        title=title,
        kind=ContentKind.AUDIOBOOK,
        sources=(LocalFileSource(Path(f"/media/{title}.mp3")),),
        duration=timedelta(minutes=10),
    )


class ApiFixture:
    def __init__(
        self,
        tmp_path: Path,
        *,
        admin_dir: Path | None = None,
        development_origins: tuple[str, ...] = (),
        physical_controls: bool = False,
    ) -> None:
        self.library = FakeLibrary()
        self.settings_store = FakeSettingsStore()
        self.inputs = FakeInputBus()
        self.physical = PhysicalControls()
        self.controls = (
            MappedInputBus(self.physical, self.settings_store) if physical_controls else None
        )
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
            auth=AdminAuth(credential_path=tmp_path / "admin-auth.json", inputs=self.inputs),
            device_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            data_dir=tmp_path,
            admin_dir=admin_dir,
            development_origins=development_origins,
            controls=self.controls,
        )
        self.client = TestClient(create_app(self.context))


def test_every_management_resource_requires_management_authority(tmp_path: Path) -> None:
    api = ApiFixture(tmp_path)
    response = api.client.get("/api/v1/device")
    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "authentication_required",
            "message": "Authentication is required.",
            "details": None,
        }
    }
    assert api.client.get("/api/v1/device", headers=HEADERS).status_code == 200


def test_built_admin_client_is_served_with_spa_fallback_without_masking_api(
    tmp_path: Path,
) -> None:
    admin = tmp_path / "admin"
    admin.mkdir()
    (admin / "index.html").write_text("<h1>AQENO Admin</h1>")
    (admin / "app.js").write_text("console.log('aqeno')")
    api = ApiFixture(tmp_path, admin_dir=admin)

    assert "AQENO Admin" in api.client.get("/").text
    assert "AQENO Admin" in api.client.get("/library/some-media").text
    assert "console.log" in api.client.get("/app.js").text
    assert api.client.get("/api/v1/does-not-exist").status_code == 404


def test_vite_development_origin_has_bounded_cors_access(tmp_path: Path) -> None:
    api = ApiFixture(tmp_path, development_origins=("http://127.0.0.1:5173",))
    response = api.client.options(
        "/api/v1/device",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-AQENO-CSRF",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    assert response.headers["access-control-allow-credentials"] == "true"
    denied = api.client.options(
        "/api/v1/device",
        headers={"Origin": "https://example.invalid", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in denied.headers


def _configure_admin(api: ApiFixture, password: str = "eine gute passphrase") -> str:
    started = api.client.post("/api/v1/auth/setup/confirmations")
    assert started.status_code == 201
    confirmation_id = started.json()["id"]
    api.inputs.emit(Previous())
    api.inputs.emit(TogglePlayback())
    api.inputs.emit(Next())
    assert (
        api.client.get(f"/api/v1/auth/setup/confirmations/{confirmation_id}").json()["state"]
        == "confirmed"
    )
    configured = api.client.post(
        "/api/v1/auth/setup",
        json={"confirmation_id": confirmation_id, "password": password},
    )
    assert configured.status_code == 201
    return str(configured.json()["csrf_token"])


def test_first_setup_uses_physical_confirmation_and_never_returns_management_key(
    tmp_path: Path,
) -> None:
    api = ApiFixture(tmp_path)
    assert api.client.get("/api/v1/auth/status").json() == {
        "setup_required": True,
        "authenticated": False,
        "physical_confirmation_available": True,
        "csrf_token": None,
    }
    csrf = _configure_admin(api)
    assert csrf
    assert api.client.get("/api/v1/device").status_code == 200
    assert api.client.get("/api/v1/auth/status").json()["authenticated"] is True
    assert "management_key" not in api.client.get("/api/openapi.json").text
    cookie = api.client.cookies.get("aqeno_admin_session")
    assert cookie is not None


def test_session_mutations_require_csrf_and_logout_invalidates_session(tmp_path: Path) -> None:
    api = ApiFixture(tmp_path)
    csrf = _configure_admin(api)
    assert api.client.post("/api/v1/token-captures").status_code == 403
    assert (
        api.client.post("/api/v1/token-captures", headers={"X-AQENO-CSRF": csrf}).status_code == 201
    )
    assert api.client.post("/api/v1/auth/logout").status_code == 403
    assert api.client.post("/api/v1/auth/logout", headers={"X-AQENO-CSRF": csrf}).status_code == 204
    assert api.client.get("/api/v1/device").status_code == 401


def test_password_login_change_and_recovery_are_local_and_profile_independent(
    tmp_path: Path,
) -> None:
    api = ApiFixture(tmp_path)
    csrf = _configure_admin(api, "erstes passwort")
    changed = api.client.post(
        "/api/v1/auth/password",
        headers={"X-AQENO-CSRF": csrf},
        json={"current_password": "erstes passwort", "new_password": "zweites passwort"},
    )
    assert changed.status_code == 200
    new_csrf = changed.json()["csrf_token"]
    api.client.post("/api/v1/auth/logout", headers={"X-AQENO-CSRF": new_csrf})
    assert (
        api.client.post("/api/v1/auth/login", json={"password": "erstes passwort"}).status_code
        == 401
    )
    assert (
        api.client.post("/api/v1/auth/login", json={"password": "zweites passwort"}).status_code
        == 200
    )

    recovery = api.client.post("/api/v1/auth/recovery/confirmations").json()
    api.inputs.emit(Previous())
    api.inputs.emit(TogglePlayback())
    api.inputs.emit(Next())
    recovered = api.client.post(
        "/api/v1/auth/recovery",
        json={"confirmation_id": recovery["id"], "password": "drittes passwort"},
    )
    assert recovered.status_code == 200


def test_hidden_management_key_can_confirm_bootstrap_without_entering_openapi(
    tmp_path: Path,
) -> None:
    api = ApiFixture(tmp_path)
    started = api.client.post("/api/v1/auth/setup/confirmations", headers=HEADERS)
    assert started.status_code == 201
    assert started.json()["state"] == "confirmed"
    configured = api.client.post(
        "/api/v1/auth/setup",
        json={"confirmation_id": started.json()["id"], "password": "diagnose passphrase"},
    )
    assert configured.status_code == 201
    cookie = configured.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=strict" in cookie
    assert "path=/api/v1" in cookie
    specification = api.client.get("/api/openapi.json").text
    assert "X-AQENO-Management-Key" not in specification
    assert "management_key" not in specification


def test_openapi_documents_browser_session_and_write_only_passwords(tmp_path: Path) -> None:
    api = ApiFixture(tmp_path)
    specification = api.client.get("/api/openapi.json").json()
    assert specification["components"]["securitySchemes"]["AdminSession"] == {
        "type": "apiKey",
        "description": "HttpOnly session cookie issued by password login or confirmed local setup.",
        "in": "cookie",
        "name": "aqeno_admin_session",
    }
    assert {"AdminSession": []} in specification["paths"]["/api/v1/device"]["get"]["security"]
    assert specification["components"]["schemas"]["PasswordRequest"]["properties"]["password"][
        "writeOnly"
    ]
    headers = specification["paths"]["/api/v1/auth/logout"]["post"]["parameters"]
    assert any(item["name"] == "X-AQENO-CSRF" and item["in"] == "header" for item in headers)


def test_validation_errors_never_echo_password_payloads(tmp_path: Path) -> None:
    api = ApiFixture(tmp_path)
    secret = "not-for-logs-or-responses-" * 100
    response = api.client.post("/api/v1/auth/login", json={"password": secret})
    assert response.status_code == 422
    assert secret not in response.text


def test_login_rate_limit_is_temporary_and_has_stable_error(tmp_path: Path) -> None:
    api = ApiFixture(tmp_path)
    csrf = _configure_admin(api)
    api.client.post("/api/v1/auth/logout", headers={"X-AQENO-CSRF": csrf})
    for _ in range(5):
        response = api.client.post("/api/v1/auth/login", json={"password": "falsch falsch"})
        assert response.status_code == 401
    limited = api.client.post("/api/v1/auth/login", json={"password": "eine gute passphrase"})
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "auth_rate_limited"


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


def test_token_capture_can_be_cancelled(tmp_path: Path) -> None:
    api = ApiFixture(tmp_path)
    capture_id = api.client.post("/api/v1/token-captures", headers=HEADERS).json()["id"]
    cancelled = api.client.delete(f"/api/v1/token-captures/{capture_id}", headers=HEADERS)
    assert cancelled.status_code == 200
    assert cancelled.json()["state"] == "cancelled"


def test_settings_are_product_schemas_and_persist_atomically_through_store(tmp_path: Path) -> None:
    api = ApiFixture(tmp_path, physical_controls=True)
    assert api.controls is not None
    api.controls.update_binding(
        LogicalControl.PRIMARY_RIGHT,
        ControlEventType.SHORT_PRESS,
        "playback.play_pause",
    )
    current = api.client.get("/api/v1/settings", headers=HEADERS).json()
    assert "controls" not in current
    current["volume"]["child_maximum"] = 60
    saved = api.client.put("/api/v1/settings", json=current, headers=HEADERS)
    assert saved.status_code == 200
    assert api.settings_store.load().volume.child_maximum == 60
    assert (
        next(
            item
            for item in api.controls.bindings()
            if item.control is LogicalControl.PRIMARY_RIGHT
            and item.event is ControlEventType.SHORT_PRESS
        ).action_id
        == "playback.play_pause"
    )
    assert saved.json()["apply_mode"] == "restart_required"


def test_physical_controls_are_capability_driven_and_persist_immediately(tmp_path: Path) -> None:
    api = ApiFixture(tmp_path, physical_controls=True)
    resource = api.client.get("/api/v1/controls", headers=HEADERS)
    assert resource.status_code == 200
    body = resource.json()
    encoder = next(item for item in body["controls"] if item["id"] == "primary_encoder")
    assert encoder == {
        "id": "primary_encoder",
        "type": "rotary_encoder",
        "label": "Drehknopf",
        "events": ["rotate_left", "rotate_right", "short_press", "long_press"],
        "illumination": True,
    }

    changed = api.client.patch(
        "/api/v1/controls/primary_encoder/mappings/long_press",
        json={"action_id": "playback.stop"},
        headers=HEADERS,
    )
    assert changed.status_code == 200
    assert any(
        item
        == {
            "control_id": "primary_encoder",
            "event": "long_press",
            "action_id": "playback.stop",
            "supported": True,
        }
        for item in changed.json()["mappings"]
    )

    # ADR 0024 § A4: with navigation waking the panel, no long-press wake exists.
    timed_wake = api.client.patch(
        "/api/v1/controls/primary_encoder/mappings/long_press",
        json={"action_id": "display.wake"},
        headers=HEADERS,
    )
    assert timed_wake.status_code == 422
    assert timed_wake.json()["error"]["code"] == "invalid_control_mapping"

    incompatible = api.client.patch(
        "/api/v1/controls/primary_encoder/mappings/rotate_left",
        json={"action_id": "playback.next"},
        headers=HEADERS,
    )
    assert incompatible.status_code == 422
    assert incompatible.json()["error"]["code"] == "invalid_control_mapping"

    reset = api.client.post("/api/v1/controls/reset", headers=HEADERS)
    assert reset.status_code == 200
    assert any(
        item["control_id"] == "primary_encoder"
        and item["event"] == "long_press"
        and item["action_id"] is None
        for item in reset.json()["mappings"]
    )


def test_openapi_is_the_complete_client_boundary_and_excludes_future_cloud(tmp_path: Path) -> None:
    api = ApiFixture(tmp_path)
    schema = api.client.get("/api/openapi.json").json()
    paths = schema["paths"]
    assert "/api/v1/imports" in paths
    assert "/api/v1/token-captures/{capture_id}/assignment" in paths
    assert "/api/v1/library/media" in paths
    assert "/api/v1/settings" in paths
    assert "/api/v1/controls" in paths
    assert "/api/v1/controls/{control_id}/mappings/{event}" in paths
    assert "/api/v1/controls/reset" in paths
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
