from __future__ import annotations

import os
import secrets
import uuid
from collections.abc import Callable
from pathlib import Path

from aqeno.adapters.clock import SystemClock
from aqeno.adapters.local_assets import LocalAssetStore
from aqeno.adapters.metadata.mutagen_probe import MutagenProbe
from aqeno.appliance.storage import capacity_status
from aqeno.application.control_mapping import MappedInputBus
from aqeno.application.display import DisplayService
from aqeno.application.management import (
    IngestionManagement,
    LibraryManagement,
    OperationRegistry,
    TokenAssignment,
)
from aqeno.application.playback import PlaybackSession
from aqeno.application.readiness import Readiness
from aqeno.config.paths import (
    admin_credential_path,
    artwork_dir,
    data_dir,
    media_dir,
    paths,
    state_dir,
)
from aqeno.management.api import ManagementContext
from aqeno.management.auth import AdminAuth
from aqeno.ports.input import InputBus
from aqeno.ports.persistence import Library, SettingsStore


def _local_value(path: Path, environment: str, factory: Callable[[], object]) -> str:
    supplied = os.environ.get(environment)
    if supplied:
        return supplied
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    value = str(factory())
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(value + "\n")
    return value


def build_context(
    *,
    library: Library,
    settings_store: SettingsStore,
    inputs: InputBus,
    readiness: Readiness | None = None,
    playback: PlaybackSession | None = None,
    display: DisplayService | None = None,
    capabilities: tuple[str, ...] = (),
) -> ManagementContext:
    operations = OperationRegistry()
    layout = paths()
    assets = LocalAssetStore(
        media_root=media_dir(),
        artwork_root=artwork_dir(),
        import_staging_root=layout.import_staging,
        capacity=lambda: capacity_status(layout.data_root),
    )
    assets.cleanup_interrupted_imports()
    local_state = state_dir()
    key = _local_value(
        local_state / "secrets" / "management.key",
        "AQENO_MANAGEMENT_KEY",
        lambda: secrets.token_urlsafe(32),
    )
    device_id = uuid.UUID(
        _local_value(local_state / "identity" / "device-id", "AQENO_DEVICE_ID", uuid.uuid4)
    )
    confirmation_inputs = (
        inputs.confirmation_inputs if isinstance(inputs, MappedInputBus) else inputs
    )
    auth = AdminAuth(credential_path=admin_credential_path(), inputs=confirmation_inputs)
    configured_admin = os.environ.get("AQENO_ADMIN_DIR")
    repository_admin = Path(__file__).parents[3] / "admin" / "build"
    packaged_admin = Path(__file__).parent / "static"
    admin_dir = (
        Path(configured_admin)
        if configured_admin
        else repository_admin
        if (repository_admin / "index.html").is_file()
        else packaged_admin
    )
    default_origins = (
        ""
        if layout.appliance
        else "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:4173"
    )
    development_origins = tuple(
        origin.strip()
        for origin in os.environ.get(
            "AQENO_MANAGEMENT_CORS_ORIGINS",
            default_origins,
        ).split(",")
        if origin.strip()
    )
    return ManagementContext(
        library=library,
        settings_store=settings_store,
        library_management=LibraryManagement(library),
        ingestion=IngestionManagement(
            library=library,
            probe=MutagenProbe(),
            clock=SystemClock(),
            operations=operations,
            artwork_dir=artwork_dir(),
        ),
        operations=operations,
        tokens=TokenAssignment(
            library,
            inputs,
            playback.set_token_capture_active if playback is not None else None,
        ),
        assets=assets,
        management_key=key,
        auth=auth,
        device_id=device_id,
        data_dir=data_dir(),
        readiness=readiness,
        playback=playback,
        display=display,
        controls=inputs if isinstance(inputs, MappedInputBus) else None,
        capabilities=capabilities,
        admin_dir=admin_dir,
        development_origins=development_origins,
    )
