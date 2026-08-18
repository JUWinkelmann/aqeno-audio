from __future__ import annotations

import base64
import hashlib
import json
import queue
import secrets
import shutil
import time
import uuid
from collections.abc import Iterator
from dataclasses import asdict
from datetime import timedelta
from pathlib import Path
from typing import Annotated, Any, Literal, cast

from fastapi import Depends, FastAPI, File, Header, Query, Request, Security, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.security import APIKeyCookie
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHttpException
from starlette.responses import Response
from starlette.types import Scope

from aqeno import __version__
from aqeno.adapters.local_assets import (
    InsufficientCapacityError,
    LocalAssetStore,
    UploadTooLargeError,
)
from aqeno.application.display import DisplayService
from aqeno.application.management import (
    CollectionNotFoundError,
    ConfigurationManagement,
    ContentNotFoundError,
    IngestionManagement,
    LibraryManagement,
    ManagementError,
    Operation,
    OperationRegistry,
    ProfileContentManagement,
    ProfileNotFoundError,
    TokenAssignment,
    TokenCapture,
)
from aqeno.application.playback import PlaybackSession
from aqeno.application.readiness import Readiness
from aqeno.config.defaults import Settings, validate
from aqeno.domain.access import AccessDecision, Audience, AudienceMode, Collection, CollectionId
from aqeno.domain.content import ContentId, ContentItem, ContentKind, HttpSource, LocalFileSource
from aqeno.domain.profile import DisplayPolicy, Profile, VolumeLimits
from aqeno.management.auth import (
    CONFIRMATION_LIFETIME_SECONDS,
    SESSION_LIFETIME_SECONDS,
    AdminAuth,
    AuthError,
    ConfirmationError,
    PasswordInvalidError,
    PasswordPolicyError,
    RateLimitError,
    SetupStateError,
)
from aqeno.management.schemas import (
    AudienceResource,
    AuthStatus,
    BrightnessSettings,
    BulkAccessRequest,
    BulkAccessResult,
    Chapter,
    CollectionResource,
    CollectionWrite,
    ConfirmationResponse,
    DeviceStatus,
    DiagnosticsStatus,
    DisplaySettings,
    EffectiveAccessResource,
    ErrorBody,
    ErrorResponse,
    FavoriteResource,
    InitialPasswordRequest,
    LibrarySettings,
    MediaDetail,
    MediaPage,
    MediaPatch,
    MediaSourceResource,
    MediaSummary,
    NfcSettings,
    OperationResponse,
    PasswordChangeRequest,
    PasswordRequest,
    PlaybackStatus,
    ProfileDisplay,
    ProfileResource,
    ProfileVolume,
    ProgressResource,
    ResumeSettings,
    SessionResponse,
    SettingsResource,
    SleepTimerSettings,
    SourceSummary,
    TokenAssignmentRequest,
    TokenCaptureResponse,
    TokenResource,
    VolumeSettings,
)
from aqeno.ports.persistence import ContentQuery, Library, SettingsStore

ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    413: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
    507: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}


class EventBroker:
    def __init__(self) -> None:
        self._subscribers: list[queue.Queue[dict[str, Any]]] = []

    def publish(self, event_type: str, data: dict[str, Any]) -> None:
        event = {"type": event_type, "data": data}
        for subscriber in tuple(self._subscribers):
            subscriber.put(event)

    def stream(self) -> Iterator[str]:
        subscriber: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=100)
        self._subscribers.append(subscriber)
        try:
            yield "event: connected\ndata: {}\n\n"
            while True:
                try:
                    event = subscriber.get(timeout=15)
                except queue.Empty:
                    yield ": keepalive\n\n"
                    continue
                yield f"event: {event['type']}\ndata: {json.dumps(event['data'])}\n\n"
        finally:
            self._subscribers.remove(subscriber)


class ManagementContext:
    def __init__(
        self,
        *,
        library: Library,
        settings_store: SettingsStore,
        library_management: LibraryManagement,
        ingestion: IngestionManagement,
        operations: OperationRegistry,
        tokens: TokenAssignment,
        assets: LocalAssetStore,
        management_key: str,
        auth: AdminAuth,
        device_id: uuid.UUID,
        data_dir: Path,
        readiness: Readiness | None = None,
        playback: PlaybackSession | None = None,
        display: DisplayService | None = None,
        capabilities: tuple[str, ...] = (),
        admin_dir: Path | None = None,
        development_origins: tuple[str, ...] = (),
    ) -> None:
        self.library = library
        self.settings_store = settings_store
        self.library_management = library_management
        self.ingestion = ingestion
        self.operations = operations
        self.tokens = tokens
        self.assets = assets
        self.management_key = management_key
        self.auth = auth
        self.device_id = device_id
        self.data_dir = data_dir
        self.readiness = readiness
        self.playback = playback
        self.display = display
        self.capabilities = capabilities
        self.admin_dir = admin_dir
        self.development_origins = development_origins
        self.configuration = ConfigurationManagement(library, settings_store)
        self.profile_content = ProfileContentManagement(library)
        self.events = EventBroker()
        operations.on_changed(self._operation_changed)
        tokens.on_changed(self._token_changed)
        if playback is not None:
            playback.on_changed(
                lambda snapshot: self.events.publish(
                    "playback.changed", {"state": snapshot.transport.value}
                )
            )

    def _operation_changed(self, operation: Operation) -> None:
        self.events.publish(
            "operation.changed",
            {"id": str(operation.id), "type": operation.type.value, "state": operation.state.value},
        )

    def _token_changed(self, capture: TokenCapture) -> None:
        self.events.publish(
            "token.capture_changed",
            {"id": str(capture.id), "state": capture.state.value, "token_uid": capture.token_uid},
        )


def create_app(context: ManagementContext) -> FastAPI:
    app = FastAPI(
        title="AQENO Local Management API",
        version="1.0.0",
        description="Local-first AQENO ownership and administration contract.",
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url=None,
        responses={401: {"model": ErrorResponse}},
    )
    if context.development_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(context.development_origins),
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Content-Type", "X-AQENO-CSRF"],
        )

    session_cookie = APIKeyCookie(
        name="aqeno_admin_session",
        scheme_name="AdminSession",
        description="HttpOnly session cookie issued by password login or confirmed local setup.",
        auto_error=False,
    )

    def require_management(
        request: Request,
        browser_session: str | None = Security(session_cookie),
        csrf: str | None = Header(default=None, alias="X-AQENO-CSRF"),
    ) -> None:
        # Deliberately absent from OpenAPI: this is a break-glass/machine path,
        # not the human-facing browser authentication contract.
        supplied_key = request.headers.get("X-AQENO-Management-Key")
        if supplied_key is not None and secrets.compare_digest(
            supplied_key, context.management_key
        ):
            return
        session = context.auth.session(browser_session)
        if session is None:
            raise ApiError(401, "authentication_required", "Authentication is required.")
        if request.method not in {"GET", "HEAD", "OPTIONS"} and (
            csrf is None or not secrets.compare_digest(csrf, session.csrf_token)
        ):
            raise ApiError(403, "csrf_required", "The request could not be verified.")

    def has_break_glass_authority(request: Request) -> bool:
        supplied_key = request.headers.get("X-AQENO-Management-Key")
        return supplied_key is not None and secrets.compare_digest(
            supplied_key, context.management_key
        )

    auth = [Depends(require_management)]

    def set_session_cookie(response: Response, request: Request, token: str) -> None:
        response.set_cookie(
            "aqeno_admin_session",
            token,
            max_age=SESSION_LIFETIME_SECONDS,
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="strict",
            path="/api/v1",
        )

    @app.exception_handler(ApiError)
    def api_error(_request: Request, exc: ApiError) -> JSONResponse:
        return _error(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(ManagementError)
    def management_error(_request: Request, exc: ManagementError) -> JSONResponse:
        status = (
            404
            if isinstance(
                exc, ContentNotFoundError | ProfileNotFoundError | CollectionNotFoundError
            )
            else 409
        )
        return _error(status, exc.code, str(exc))

    @app.exception_handler(AuthError)
    def auth_error(_request: Request, exc: AuthError) -> JSONResponse:
        if isinstance(exc, RateLimitError):
            return _error(
                429,
                exc.code,
                "Too many attempts. Try again shortly.",
                {"retry_after_seconds": exc.retry_after_seconds},
            )
        if isinstance(exc, PasswordInvalidError):
            return _error(401, exc.code, "The password is not correct.")
        if isinstance(exc, PasswordPolicyError):
            return _error(422, exc.code, str(exc))
        if isinstance(exc, ConfirmationError):
            return _error(409, exc.code, str(exc))
        if isinstance(exc, SetupStateError):
            return _error(409, exc.code, str(exc))
        return _error(400, exc.code, "Authentication failed.")

    @app.get("/api/v1/auth/status", response_model=AuthStatus, tags=["authentication"])
    def auth_status(request: Request) -> AuthStatus:
        session = context.auth.session(request.cookies.get("aqeno_admin_session"))
        return AuthStatus(
            setup_required=not context.auth.configured,
            authenticated=session is not None,
            csrf_token=session.csrf_token if session is not None else None,
        )

    def confirmation_response(confirmation_id: uuid.UUID, purpose: str) -> ConfirmationResponse:
        confirmation = context.auth.confirmation(confirmation_id, purpose)
        return ConfirmationResponse(
            id=confirmation.id,
            purpose=cast(Literal["setup", "recovery"], confirmation.purpose),
            state="confirmed" if confirmation.confirmed else "pending",
            expires_in_seconds=max(0, int(confirmation.expires_at - time.monotonic())),
        )

    @app.post(
        "/api/v1/auth/setup/confirmations",
        response_model=ConfirmationResponse,
        status_code=201,
        tags=["authentication"],
    )
    def begin_setup_confirmation(request: Request) -> ConfirmationResponse:
        if context.auth.configured:
            raise SetupStateError("administration is already configured")
        confirmation = context.auth.begin_confirmation("setup")
        if has_break_glass_authority(request):
            confirmation = context.auth.confirm(confirmation.id, "setup")
        return ConfirmationResponse(
            id=confirmation.id,
            purpose="setup",
            state="confirmed" if confirmation.confirmed else "pending",
            expires_in_seconds=CONFIRMATION_LIFETIME_SECONDS,
        )

    @app.get(
        "/api/v1/auth/setup/confirmations/{confirmation_id}",
        response_model=ConfirmationResponse,
        tags=["authentication"],
    )
    def setup_confirmation(confirmation_id: uuid.UUID) -> ConfirmationResponse:
        return confirmation_response(confirmation_id, "setup")

    @app.post(
        "/api/v1/auth/setup",
        response_model=SessionResponse,
        status_code=201,
        tags=["authentication"],
    )
    def setup_password(
        body: InitialPasswordRequest, request: Request, response: Response
    ) -> SessionResponse:
        token, session = context.auth.create_initial_password(body.confirmation_id, body.password)
        set_session_cookie(response, request, token)
        return SessionResponse(
            csrf_token=session.csrf_token, expires_in_seconds=SESSION_LIFETIME_SECONDS
        )

    @app.post("/api/v1/auth/login", response_model=SessionResponse, tags=["authentication"])
    def login(body: PasswordRequest, request: Request, response: Response) -> SessionResponse:
        peer = request.client.host if request.client is not None else "local"
        token, session = context.auth.login(body.password, peer)
        set_session_cookie(response, request, token)
        return SessionResponse(
            csrf_token=session.csrf_token, expires_in_seconds=SESSION_LIFETIME_SECONDS
        )

    @app.post("/api/v1/auth/logout", status_code=204, dependencies=auth, tags=["authentication"])
    def logout(request: Request, response: Response) -> None:
        context.auth.revoke(request.cookies.get("aqeno_admin_session"))
        response.delete_cookie("aqeno_admin_session", path="/api/v1")

    @app.post(
        "/api/v1/auth/password",
        response_model=SessionResponse,
        dependencies=auth,
        tags=["authentication"],
    )
    def change_password(
        body: PasswordChangeRequest, request: Request, response: Response
    ) -> SessionResponse:
        context.auth.change_password(body.current_password, body.new_password)
        token, session = context.auth.create_session()
        set_session_cookie(response, request, token)
        return SessionResponse(
            csrf_token=session.csrf_token, expires_in_seconds=SESSION_LIFETIME_SECONDS
        )

    @app.post(
        "/api/v1/auth/recovery/confirmations",
        response_model=ConfirmationResponse,
        status_code=201,
        tags=["authentication"],
    )
    def begin_recovery_confirmation(request: Request) -> ConfirmationResponse:
        if not context.auth.configured:
            raise SetupStateError("administration setup is required")
        confirmation = context.auth.begin_confirmation("recovery")
        if has_break_glass_authority(request):
            confirmation = context.auth.confirm(confirmation.id, "recovery")
        return ConfirmationResponse(
            id=confirmation.id,
            purpose="recovery",
            state="confirmed" if confirmation.confirmed else "pending",
            expires_in_seconds=CONFIRMATION_LIFETIME_SECONDS,
        )

    @app.get(
        "/api/v1/auth/recovery/confirmations/{confirmation_id}",
        response_model=ConfirmationResponse,
        tags=["authentication"],
    )
    def recovery_confirmation(confirmation_id: uuid.UUID) -> ConfirmationResponse:
        return confirmation_response(confirmation_id, "recovery")

    @app.post(
        "/api/v1/auth/recovery",
        response_model=SessionResponse,
        tags=["authentication"],
    )
    def recover_password(
        body: InitialPasswordRequest, request: Request, response: Response
    ) -> SessionResponse:
        token, session = context.auth.recover(body.confirmation_id, body.password)
        set_session_cookie(response, request, token)
        return SessionResponse(
            csrf_token=session.csrf_token, expires_in_seconds=SESSION_LIFETIME_SECONDS
        )

    @app.exception_handler(RequestValidationError)
    def validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
        issues = [
            {key: value for key, value in issue.items() if key not in {"input", "ctx"}}
            for issue in exc.errors()
        ]
        return _error(422, "validation_failed", "The request is not valid.", {"issues": issues})

    @app.get("/api/v1/device", response_model=DeviceStatus, dependencies=auth, tags=["device"])
    def device() -> DeviceStatus:
        usage = shutil.disk_usage(context.data_dir)
        readiness = context.readiness.current.name.lower() if context.readiness else "local_ready"
        capabilities = sorted(
            {"library", "media_import", "token_assignment", *context.capabilities}
        )
        return DeviceStatus(
            device_id=context.device_id,
            name="AQENO",
            aqeno_version=__version__,
            readiness=readiness,
            database_health=context.library.health().value,
            capabilities=capabilities,
            storage_total_bytes=usage.total,
            storage_free_bytes=usage.free,
        )

    @app.get(
        "/api/v1/diagnostics",
        response_model=DiagnosticsStatus,
        dependencies=auth,
        tags=["device"],
    )
    def diagnostics() -> DiagnosticsStatus:
        playback_error = None
        if context.playback is not None and context.playback.last_failure is not None:
            playback_error = context.playback.last_failure.code.value
        return DiagnosticsStatus(
            functional=context.library.health().value == "ok",
            readiness=(
                context.readiness.current.name.lower() if context.readiness else "local_ready"
            ),
            database=context.library.health().value,
            storage_writable=context.library.health().value == "ok",
            audio="ready" if context.playback is not None else "not_reported",
            display="ready" if context.display is not None else "not_reported",
            nfc="ready" if "nfc" in context.capabilities else "simulated_or_absent",
            physical_controls=(
                "ready" if "physical_controls" in context.capabilities else "not_reported"
            ),
            last_playback_error=playback_error,
        )

    @app.get(
        "/api/v1/media-sources",
        response_model=list[MediaSourceResource],
        dependencies=auth,
        tags=["library"],
    )
    def media_sources() -> list[MediaSourceResource]:
        settings = context.settings_store.load()
        internal = context.assets.media_root.resolve()
        return [
            MediaSourceResource(
                id=hashlib.sha256(str(root).encode()).hexdigest()[:16],
                kind="local" if root.resolve() == internal else "mounted_external",
                path=str(root),
                available=root.is_dir(),
            )
            for root in settings.library.roots
        ]

    @app.get(
        "/api/v1/library/media",
        response_model=MediaPage,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["library"],
    )
    def list_media(
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
        cursor: str | None = None,
        search: Annotated[str | None, Query(max_length=200)] = None,
        kind: ContentKind | None = None,
        available: bool | None = None,
        profile_name: str | None = None,
    ) -> MediaPage:
        after = _decode_cursor(cursor) if cursor else None
        page = context.library_management.query(
            ContentQuery(
                limit=limit + 1,
                search=search,
                kind=kind,
                available=available,
                after=after,
                profile_name=profile_name,
            )
        )
        visible = page.items[:limit]
        next_cursor = _encode_cursor(visible[-1]) if len(page.items) > limit and visible else None
        return MediaPage(
            items=[_media_summary(item) for item in visible],
            next_cursor=next_cursor,
            total=page.total,
        )

    @app.get(
        "/api/v1/library/media/{media_id}",
        response_model=MediaDetail,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["library"],
    )
    def get_media(media_id: uuid.UUID, profile: str | None = None) -> MediaDetail:
        item = context.library_management.get(ContentId(media_id))
        resume = context.library.get_resume(item.id, profile) if profile is not None else None
        return _media_detail(item, context.assets.media_root, resume)

    @app.patch(
        "/api/v1/library/media/{media_id}",
        response_model=MediaDetail,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["library"],
    )
    def patch_media(media_id: uuid.UUID, patch: MediaPatch) -> MediaDetail:
        item = context.library_management.update_metadata(
            ContentId(media_id), title=patch.title, kind=patch.kind, language=patch.language
        )
        return _media_detail(item, context.assets.media_root, None)

    @app.delete(
        "/api/v1/library/media/{media_id}",
        status_code=204,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["library"],
    )
    def delete_media(media_id: uuid.UUID) -> None:
        context.library_management.remove(ContentId(media_id))

    @app.get(
        "/api/v1/library/media/{media_id}/artwork",
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["artwork"],
    )
    def artwork(media_id: uuid.UUID) -> FileResponse:
        item = context.library_management.get(ContentId(media_id))
        if item.artwork is None or not item.artwork.is_file():
            raise ApiError(404, "artwork_not_found", "This media object has no artwork.")
        return FileResponse(item.artwork)

    @app.put(
        "/api/v1/library/media/{media_id}/artwork",
        response_model=MediaDetail,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["artwork"],
    )
    def put_artwork(media_id: uuid.UUID, file: Annotated[UploadFile, File()]) -> MediaDetail:
        suffix = Path(file.filename or "").suffix
        try:
            path = context.assets.store_artwork(file.file, content_id=media_id, extension=suffix)
        except InsufficientCapacityError as exc:
            raise ApiError(507, "storage_capacity_critical", str(exc)) from exc
        except UploadTooLargeError as exc:
            raise ApiError(413, "upload_too_large", str(exc)) from exc
        except ValueError as exc:
            raise ApiError(400, "artwork_type_unsupported", str(exc)) from exc
        item = context.library_management.set_artwork(ContentId(media_id), path)
        return _media_detail(item, context.assets.media_root, None)

    @app.delete(
        "/api/v1/library/media/{media_id}/artwork",
        response_model=MediaDetail,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["artwork"],
    )
    def delete_artwork(media_id: uuid.UUID) -> MediaDetail:
        item = context.library_management.get(ContentId(media_id))
        old_path = item.artwork
        updated = context.library_management.set_artwork(item.id, None)
        if old_path is not None and old_path.parent == context.assets.artwork_root:
            context.assets.remove_artwork(old_path)
        return _media_detail(updated, context.assets.media_root, None)

    @app.post(
        "/api/v1/imports",
        response_model=OperationResponse,
        status_code=202,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["ingestion"],
    )
    def import_media(file: Annotated[UploadFile, File()]) -> OperationResponse:
        if not file.filename:
            raise ApiError(400, "upload_filename_missing", "A filename is required.")
        try:
            stored = context.assets.store_media(file.file, filename=file.filename)
        except InsufficientCapacityError as exc:
            raise ApiError(507, "storage_capacity_critical", str(exc)) from exc
        except UploadTooLargeError as exc:
            raise ApiError(413, "upload_too_large", str(exc)) from exc
        operation = context.ingestion.scan((stored.parent,), imported=True)
        return _operation(operation)

    @app.post(
        "/api/v1/library/scans",
        response_model=OperationResponse,
        status_code=202,
        dependencies=auth,
        tags=["ingestion"],
    )
    def scan_library() -> OperationResponse:
        settings = context.settings_store.load()
        return _operation(context.ingestion.scan(settings.library.roots))

    @app.get(
        "/api/v1/operations",
        response_model=list[OperationResponse],
        dependencies=auth,
        tags=["operations"],
    )
    def operations() -> list[OperationResponse]:
        return [_operation(item) for item in context.operations.list()]

    @app.get(
        "/api/v1/operations/{operation_id}",
        response_model=OperationResponse,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["operations"],
    )
    def operation(operation_id: uuid.UUID) -> OperationResponse:
        found = context.operations.get(operation_id)
        if found is None:
            raise ApiError(404, "operation_not_found", "No such operation.")
        return _operation(found)

    @app.get(
        "/api/v1/tokens",
        response_model=list[TokenResource],
        dependencies=auth,
        tags=["tokens"],
    )
    def tokens() -> list[TokenResource]:
        return [
            TokenResource(uid=mapping.uid, assigned_media_id=mapping.content_id.value)
            for mapping in context.library.list_tags()
        ]

    @app.get(
        "/api/v1/tokens/{uid}",
        response_model=TokenResource,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["tokens"],
    )
    def token(uid: str) -> TokenResource:
        content_id = context.library.resolve_tag(uid)
        if content_id is None:
            raise ApiError(404, "token_not_found", "No assigned token with this identifier.")
        return TokenResource(uid=uid, assigned_media_id=content_id.value)

    @app.delete(
        "/api/v1/tokens/{uid}/assignment",
        status_code=204,
        dependencies=auth,
        tags=["tokens"],
    )
    def remove_assignment(uid: str) -> None:
        context.library.unmap_tag(uid)

    @app.post(
        "/api/v1/token-captures",
        response_model=TokenCaptureResponse,
        status_code=201,
        dependencies=auth,
        tags=["tokens"],
    )
    def start_capture() -> TokenCaptureResponse:
        return _capture(context.tokens.start_capture())

    @app.get(
        "/api/v1/token-captures/{capture_id}",
        response_model=TokenCaptureResponse,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["tokens"],
    )
    def get_capture(capture_id: uuid.UUID) -> TokenCaptureResponse:
        return _capture(context.tokens.get_capture(capture_id))

    @app.delete(
        "/api/v1/token-captures/{capture_id}",
        response_model=TokenCaptureResponse,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["tokens"],
    )
    def cancel_capture(capture_id: uuid.UUID) -> TokenCaptureResponse:
        return _capture(context.tokens.cancel(capture_id))

    @app.put(
        "/api/v1/token-captures/{capture_id}/assignment",
        response_model=TokenCaptureResponse,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["tokens"],
    )
    def assign_capture(
        capture_id: uuid.UUID, assignment: TokenAssignmentRequest
    ) -> TokenCaptureResponse:
        return _capture(context.tokens.assign(capture_id, ContentId(assignment.media_id)))

    @app.get(
        "/api/v1/playback",
        response_model=PlaybackStatus,
        dependencies=auth,
        tags=["playback"],
    )
    def playback() -> PlaybackStatus:
        if context.playback is None:
            return PlaybackStatus(
                state="not_reported",
                media_id=None,
                title=None,
                chapter_title=None,
                position_seconds=None,
                duration_seconds=None,
                volume=None,
                failure_code=None,
            )
        snapshot = context.playback.snapshot
        return PlaybackStatus(
            state=snapshot.transport.value,
            media_id=snapshot.content_id.value if snapshot.content_id else None,
            title=snapshot.title,
            chapter_title=snapshot.chapter_title,
            position_seconds=_seconds(snapshot.position),
            duration_seconds=_seconds(snapshot.duration),
            volume=snapshot.volume,
            failure_code=snapshot.failure_code.value if snapshot.failure_code else None,
        )

    @app.get(
        "/api/v1/settings",
        response_model=SettingsResource,
        dependencies=auth,
        tags=["configuration"],
    )
    def settings() -> SettingsResource:
        return _settings_resource(context.configuration.settings())

    @app.put(
        "/api/v1/settings",
        response_model=SettingsResource,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["configuration"],
    )
    def put_settings(resource: SettingsResource) -> SettingsResource:
        raw = resource.model_dump(exclude={"apply_mode"})
        configured, warnings = validate(raw)
        if warnings:
            raise ApiError(
                422,
                "settings_out_of_range",
                "Settings violate AQENO limits.",
                {"warnings": warnings},
            )
        context.configuration.save_settings(configured)
        return _settings_resource(configured)

    @app.get(
        "/api/v1/profiles",
        response_model=list[ProfileResource],
        dependencies=auth,
        tags=["configuration"],
    )
    def profiles() -> list[ProfileResource]:
        return [_profile_resource(profile) for profile in context.configuration.profiles()]

    @app.delete(
        "/api/v1/profiles/{name}",
        status_code=204,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["configuration"],
    )
    def delete_profile(name: str) -> None:
        context.configuration.remove_profile(name)

    @app.get(
        "/api/v1/profiles/{name}",
        response_model=ProfileResource,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["configuration"],
    )
    def profile(name: str) -> ProfileResource:
        found = context.configuration.profile(name)
        if found is None:
            raise ApiError(404, "profile_not_found", "No such profile.")
        return _profile_resource(found)

    @app.put(
        "/api/v1/profiles/{name}",
        response_model=ProfileResource,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["configuration"],
    )
    async def put_profile(name: str, resource: ProfileResource) -> ProfileResource:
        if name != resource.name:
            raise ApiError(409, "profile_name_mismatch", "Path and body profile names differ.")
        display = resource.display
        volume = resource.volume
        try:
            saved = context.configuration.save_profile(
                name=name,
                level=resource.level,
                role=resource.role,
                display=DisplayPolicy(
                    inactivity_timeout=timedelta(seconds=display.inactivity_timeout_seconds),
                    night_timeout=timedelta(seconds=display.night_timeout_seconds),
                    allows_dim=display.allows_dim,
                    dim_hold=(
                        timedelta(seconds=display.dim_hold_seconds)
                        if display.dim_hold_seconds is not None
                        else None
                    ),
                    interactive_brightness=display.interactive_brightness,
                    dim_brightness=display.dim_brightness,
                    ambient_brightness=display.ambient_brightness,
                    night_brightness=display.night_brightness,
                    led_brightness=display.led_brightness,
                ),
                volume=VolumeLimits(
                    maximum=volume.maximum,
                    night_maximum=volume.night_maximum,
                    headphone_maximum=volume.headphone_maximum,
                ),
                ambient_enabled=resource.ambient_enabled,
            )
        except ValueError as exc:
            raise ApiError(422, "profile_policy_invalid", str(exc)) from exc
        return _profile_resource(saved)

    @app.get(
        "/api/v1/profiles/{name}/favorites",
        response_model=MediaPage,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["profiles"],
    )
    def favorites(
        name: str,
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
        cursor: str | None = None,
    ) -> MediaPage:
        if context.configuration.profile(name) is None:
            raise ProfileNotFoundError(name)
        after = _decode_cursor(cursor) if cursor else None
        page = context.library.list_favorites(
            name, ContentQuery(limit=limit + 1, after=after, available=True)
        )
        visible = page.items[:limit]
        return MediaPage(
            items=[_media_summary(item) for item in visible],
            next_cursor=(
                _encode_cursor(visible[-1]) if len(page.items) > limit and visible else None
            ),
            total=page.total,
        )

    @app.put(
        "/api/v1/profiles/{name}/favorites/{media_id}",
        response_model=FavoriteResource,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["profiles"],
    )
    def set_favorite(name: str, media_id: uuid.UUID) -> FavoriteResource:
        context.profile_content.set_favorite(name, ContentId(media_id), True)
        return FavoriteResource(profile_name=name, media_id=media_id, favorite=True)

    @app.delete(
        "/api/v1/profiles/{name}/favorites/{media_id}",
        response_model=FavoriteResource,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["profiles"],
    )
    def remove_favorite(name: str, media_id: uuid.UUID) -> FavoriteResource:
        context.profile_content.set_favorite(name, ContentId(media_id), False)
        return FavoriteResource(profile_name=name, media_id=media_id, favorite=False)

    @app.get(
        "/api/v1/profiles/{name}/progress/{media_id}",
        response_model=ProgressResource,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["profiles"],
    )
    def progress(name: str, media_id: uuid.UUID) -> ProgressResource:
        if context.configuration.profile(name) is None:
            raise ProfileNotFoundError(name)
        context.library_management.get(ContentId(media_id))
        position = context.library.get_resume(ContentId(media_id), name)
        return ProgressResource(
            profile_name=name, media_id=media_id, position_seconds=_seconds(position)
        )

    @app.post(
        "/api/v1/content-access/bulk",
        response_model=BulkAccessResult,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["access"],
    )
    async def bulk_access(request: BulkAccessRequest) -> BulkAccessResult:
        content_ids = tuple(ContentId(media_id) for media_id in request.media_ids)
        profiles = tuple(dict.fromkeys(request.profile_names))
        if request.operation == "set_shared":
            context.profile_content.set_audience(content_ids, Audience(mode=AudienceMode.SHARED))
        elif request.operation == "set_selected_profiles":
            if not profiles:
                raise ApiError(
                    422,
                    "profiles_required",
                    "Selected-profile audience requires at least one profile.",
                )
            context.profile_content.set_audience(
                content_ids,
                Audience(mode=AudienceMode.SELECTED_PROFILES, profile_names=profiles),
            )
        else:
            if not profiles:
                raise ApiError(422, "profiles_required", "This operation requires profiles.")
            decision = {
                "allow": AccessDecision.ALLOW,
                "deny": AccessDecision.DENY,
                "clear_override": None,
            }[request.operation]
            context.profile_content.set_overrides(content_ids, profiles, decision)
        return BulkAccessResult(
            media_count=len(content_ids),
            profile_count=len(profiles),
            operation=request.operation,
        )

    @app.get(
        "/api/v1/library/media/{media_id}/access/{profile_name}",
        response_model=EffectiveAccessResource,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["access"],
    )
    def effective_access(media_id: uuid.UUID, profile_name: str) -> EffectiveAccessResource:
        content_id = ContentId(media_id)
        effective = context.profile_content.effective(content_id, profile_name)
        audience = context.library.get_content_audience(content_id)
        return EffectiveAccessResource(
            media_id=media_id,
            profile_name=profile_name,
            allowed=effective.allowed,
            source=effective.source,
            explicit_decision=effective.explicit_decision,
            inherited_collection_ids=[item.value for item in effective.inherited_collection_ids],
            media_audience=_audience_resource(audience) if audience else None,
        )

    @app.get(
        "/api/v1/collections",
        response_model=list[CollectionResource],
        dependencies=auth,
        tags=["collections"],
    )
    def collections() -> list[CollectionResource]:
        return [_collection_resource(context, item) for item in context.library.list_collections()]

    @app.post(
        "/api/v1/collections",
        response_model=CollectionResource,
        status_code=201,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["collections"],
    )
    async def create_collection(resource: CollectionWrite) -> CollectionResource:
        collection = Collection(
            id=CollectionId(),
            name=resource.name,
            content_ids=tuple(ContentId(item) for item in resource.media_ids),
        )
        context.profile_content.save_collection(collection)
        return _collection_resource(context, collection)

    @app.put(
        "/api/v1/collections/{collection_id}",
        response_model=CollectionResource,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["collections"],
    )
    async def put_collection(
        collection_id: uuid.UUID, resource: CollectionWrite
    ) -> CollectionResource:
        collection = Collection(
            id=CollectionId(collection_id),
            name=resource.name,
            content_ids=tuple(ContentId(item) for item in resource.media_ids),
        )
        context.profile_content.save_collection(collection)
        return _collection_resource(context, collection)

    @app.delete(
        "/api/v1/collections/{collection_id}",
        status_code=204,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["collections"],
    )
    def delete_collection(collection_id: uuid.UUID) -> None:
        context.profile_content.remove_collection(CollectionId(collection_id))

    @app.put(
        "/api/v1/collections/{collection_id}/audience",
        response_model=CollectionResource,
        dependencies=auth,
        responses=ERROR_RESPONSES,
        tags=["collections", "access"],
    )
    async def put_collection_audience(
        collection_id: uuid.UUID, resource: AudienceResource
    ) -> CollectionResource:
        cid = CollectionId(collection_id)
        context.profile_content.set_collection_audience(
            cid,
            Audience(mode=resource.mode, profile_names=tuple(resource.profile_names)),
        )
        collection = context.library.get_collection(cid)
        if collection is None:
            raise CollectionNotFoundError(str(collection_id))
        return _collection_resource(context, collection)

    @app.get("/api/v1/events", dependencies=auth, tags=["events"])
    def events() -> StreamingResponse:
        return StreamingResponse(context.events.stream(), media_type="text/event-stream")

    if context.admin_dir is not None and (context.admin_dir / "index.html").is_file():
        app.mount("/", AdminSpaFiles(directory=context.admin_dir, html=True), name="admin-client")

    return app


class AdminSpaFiles(StaticFiles):
    """Serve the static Management SPA without swallowing unknown API routes."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except StarletteHttpException as exc:
            if exc.status_code != 404 or path == "api" or path.startswith("api/"):
                raise
            return await super().get_response("index.html", scope)


class ApiError(Exception):
    def __init__(
        self, status_code: int, code: str, message: str, details: dict[str, Any] | None = None
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


def _error(
    status: int, code: str, message: str, details: dict[str, Any] | None = None
) -> JSONResponse:
    body = ErrorResponse(error=ErrorBody(code=code, message=message, details=details))
    return JSONResponse(status_code=status, content=body.model_dump(mode="json"))


def _seconds(value: timedelta | None) -> float | None:
    return value.total_seconds() if value is not None else None


def _media_summary(item: ContentItem) -> MediaSummary:
    artwork = f"/api/v1/library/media/{item.id.value}/artwork" if item.artwork else None
    return MediaSummary(
        id=item.id.value,
        title=item.title,
        kind=item.kind,
        available=item.available,
        duration_seconds=_seconds(item.duration),
        language=item.language,
        artwork_thumbnail_url=artwork,
    )


def _media_detail(item: ContentItem, internal_root: Path, resume: timedelta | None) -> MediaDetail:
    summary = _media_summary(item)
    sources: list[SourceSummary] = []
    for source in item.sources:
        if isinstance(source, LocalFileSource):
            try:
                source.path.resolve().relative_to(internal_root.resolve())
                location: Literal["internal", "mounted_external", "remote"] = "internal"
            except (OSError, ValueError):
                location = "mounted_external"
            sources.append(
                SourceSummary(
                    type="local_file",
                    location=location,
                    display_name=source.path.name,
                    seekable=True,
                )
            )
        elif isinstance(source, HttpSource):
            sources.append(
                SourceSummary(
                    type="http",
                    location="remote",
                    display_name="Network stream",
                    seekable=source.seekable,
                )
            )
    return MediaDetail(
        **summary.model_dump(),
        chapters=[
            Chapter(
                id=f"{item.id.value}:{chapter.index}",
                index=chapter.index,
                title=chapter.title,
                start_seconds=chapter.start.total_seconds(),
                duration_seconds=_seconds(chapter.duration),
            )
            for chapter in item.chapters
        ],
        sources=sources,
        artwork_url=summary.artwork_thumbnail_url,
        kind_overridden=item.kind_overridden,
        last_seen=item.last_seen,
        resume_seconds=_seconds(resume),
    )


def _encode_cursor(item: ContentItem) -> str:
    raw = json.dumps([item.title.casefold(), str(item.id.value)], separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _decode_cursor(value: str) -> tuple[str, ContentId]:
    try:
        padding = "=" * (-len(value) % 4)
        title, content_id = json.loads(base64.urlsafe_b64decode(value + padding))
        if not isinstance(title, str) or not isinstance(content_id, str):
            raise ValueError
        return title, ContentId(uuid.UUID(content_id))
    except Exception as exc:
        raise ApiError(400, "cursor_invalid", "The pagination cursor is invalid.") from exc


def _operation(operation: Operation) -> OperationResponse:
    error = None
    if operation.error_code is not None:
        error = ErrorBody(code=operation.error_code, message=operation.error_message or "Failed")
    return OperationResponse(
        id=operation.id,
        type=operation.type.value,
        state=operation.state.value,
        progress=operation.progress,
        result=operation.result,
        error=error,
    )


def _capture(capture: TokenCapture) -> TokenCaptureResponse:
    return TokenCaptureResponse(
        id=capture.id,
        state=capture.state.value,
        token_uid=capture.token_uid,
        assigned_media_id=capture.content_id.value if capture.content_id else None,
    )


def _settings_resource(settings: Settings) -> SettingsResource:
    return SettingsResource(
        display=DisplaySettings(**asdict(settings.display)),
        brightness=BrightnessSettings(**asdict(settings.brightness)),
        volume=VolumeSettings(**asdict(settings.volume)),
        resume=ResumeSettings(**asdict(settings.resume)),
        sleep_timer=SleepTimerSettings(
            duration_minutes=settings.sleep_timer.duration_minutes,
            presets_minutes=list(settings.sleep_timer.presets_minutes),
            fade_out_seconds=settings.sleep_timer.fade_out_seconds,
            action_at_end=cast(Literal["pause", "stop"], settings.sleep_timer.action_at_end.value),
        ),
        nfc=NfcSettings(**asdict(settings.nfc)),
        library=LibrarySettings(
            roots=[str(root) for root in settings.library.roots],
            scan_on_startup=settings.library.scan_on_startup,
            follow_symlinks=settings.library.follow_symlinks,
        ),
        language=settings.language,  # type: ignore[arg-type]
    )


def _profile_resource(profile: Profile) -> ProfileResource:
    return ProfileResource(
        name=profile.name,
        level=profile.level,
        role=profile.role,
        display=ProfileDisplay(
            inactivity_timeout_seconds=int(profile.display.inactivity_timeout.total_seconds()),
            night_timeout_seconds=int(profile.display.night_timeout.total_seconds()),
            allows_dim=profile.display.allows_dim,
            dim_hold_seconds=(
                int(profile.display.dim_hold.total_seconds()) if profile.display.dim_hold else None
            ),
            interactive_brightness=profile.display.interactive_brightness,
            dim_brightness=profile.display.dim_brightness,
            ambient_brightness=profile.display.ambient_brightness,
            night_brightness=profile.display.night_brightness,
            led_brightness=profile.display.led_brightness,
        ),
        volume=ProfileVolume(
            maximum=profile.volume.maximum,
            night_maximum=profile.volume.night_maximum,
            headphone_maximum=profile.volume.headphone_maximum,
        ),
        ambient_enabled=profile.ambient_enabled,
    )


def _audience_resource(audience: Audience) -> AudienceResource:
    return AudienceResource(mode=audience.mode, profile_names=list(audience.profile_names))


def _collection_resource(context: ManagementContext, collection: Collection) -> CollectionResource:
    audience = context.library.get_collection_audience(collection.id)
    return CollectionResource(
        id=collection.id.value,
        name=collection.name,
        media_ids=[content_id.value for content_id in collection.content_ids],
        audience=_audience_resource(audience) if audience else None,
    )
