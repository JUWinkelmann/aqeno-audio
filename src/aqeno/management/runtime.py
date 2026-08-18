from __future__ import annotations

import os
import secrets
import uuid
from collections.abc import Callable
from pathlib import Path

from aqeno.adapters.clock import SystemClock
from aqeno.adapters.local_assets import LocalAssetStore
from aqeno.adapters.metadata.mutagen_probe import MutagenProbe
from aqeno.application.display import DisplayService
from aqeno.application.management import (
    IngestionManagement,
    LibraryManagement,
    OperationRegistry,
    TokenAssignment,
)
from aqeno.application.playback import PlaybackSession
from aqeno.application.readiness import Readiness
from aqeno.config.paths import artwork_dir, data_dir, media_dir, state_dir
from aqeno.management.api import ManagementContext
from aqeno.ports.input import InputBus
from aqeno.ports.persistence import Library, SettingsStore


def _local_value(path: Path, environment: str, factory: Callable[[], object]) -> str:
    supplied = os.environ.get(environment)
    if supplied:
        return supplied
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    path.parent.mkdir(parents=True, exist_ok=True)
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
    assets = LocalAssetStore(media_root=media_dir(), artwork_root=artwork_dir())
    local_state = state_dir()
    key = _local_value(
        local_state / "management.key",
        "AQENO_MANAGEMENT_KEY",
        lambda: secrets.token_urlsafe(32),
    )
    device_id = uuid.UUID(_local_value(local_state / "device-id", "AQENO_DEVICE_ID", uuid.uuid4))
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
        tokens=TokenAssignment(library, inputs),
        assets=assets,
        management_key=key,
        device_id=device_id,
        data_dir=data_dir(),
        readiness=readiness,
        playback=playback,
        display=display,
        capabilities=capabilities,
    )
