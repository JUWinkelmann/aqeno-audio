"""AQENO-DATA marker, validation and capacity policy."""

from __future__ import annotations

import json
import os
import shutil
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Protocol

DATA_FORMAT_VERSION = 1
VOLUME_MARKER = "volume.json"
GIB = 1024**3


class VolumeProblem(StrEnum):
    MISSING = "missing"
    NOT_MOUNTED = "not_mounted"
    READ_ONLY = "read_only"
    PERMISSION_DENIED = "permission_denied"
    MARKER_MISSING = "marker_missing"
    MARKER_INVALID = "marker_invalid"
    VERSION_UNSUPPORTED = "version_unsupported"
    LAYOUT_INVALID = "layout_invalid"


class VolumeValidationError(RuntimeError):
    def __init__(self, problem: VolumeProblem, message: str) -> None:
        super().__init__(message)
        self.problem = problem


class CapacityLevel(StrEnum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


class DiskUsage(Protocol):
    total: int
    used: int
    free: int


@dataclass(frozen=True, slots=True)
class VolumeMarker:
    data_format_version: int
    volume_id: str
    created_at: str


@dataclass(frozen=True, slots=True)
class CapacityStatus:
    level: CapacityLevel
    total_bytes: int
    free_bytes: int
    warning_below_bytes: int
    critical_below_bytes: int

    def permits(self, payload_bytes: int, *, staging_copies: int = 1) -> bool:
        required = int(payload_bytes * staging_copies * 1.10)
        return self.free_bytes - required >= self.critical_below_bytes


def capacity_status(root: Path, *, usage: DiskUsage | None = None) -> CapacityStatus:
    actual = usage or shutil.disk_usage(root)
    warning = max(int(actual.total * 0.10), 5 * GIB)
    critical = max(int(actual.total * 0.03), GIB)
    level = (
        CapacityLevel.CRITICAL
        if actual.free < critical
        else CapacityLevel.WARNING
        if actual.free < warning
        else CapacityLevel.HEALTHY
    )
    return CapacityStatus(level, actual.total, actual.free, warning, critical)


def create_volume_marker(root: Path, *, now: datetime | None = None) -> VolumeMarker:
    """Initialize only an already-created, empty provisioning target."""
    if not root.is_dir():
        raise VolumeValidationError(VolumeProblem.MISSING, f"data root does not exist: {root}")
    marker_path = root / VOLUME_MARKER
    if marker_path.exists():
        raise FileExistsError(marker_path)
    if any(root.iterdir()):
        raise VolumeValidationError(
            VolumeProblem.MARKER_MISSING, "refusing to initialize a non-empty unmarked directory"
        )
    marker = VolumeMarker(
        DATA_FORMAT_VERSION,
        str(uuid.uuid4()),
        (now or datetime.now(UTC)).isoformat().replace("+00:00", "Z"),
    )
    temporary = root / f".{VOLUME_MARKER}.partial"
    temporary.write_text(json.dumps(asdict(marker), sort_keys=True) + "\n", encoding="utf-8")
    with temporary.open("rb") as handle:
        os.fsync(handle.fileno())
    os.replace(temporary, marker_path)
    return marker


def _read_marker(root: Path) -> VolumeMarker:
    marker_path = root / VOLUME_MARKER
    if marker_path.is_symlink() or not marker_path.is_file():
        raise VolumeValidationError(VolumeProblem.MARKER_MISSING, "AQENO-DATA marker is missing")
    try:
        raw = json.loads(marker_path.read_text(encoding="utf-8"))
        created_at = str(raw["created_at"])
        parsed_created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        if parsed_created_at.tzinfo is None:
            raise ValueError("created_at has no timezone")
        marker = VolumeMarker(
            data_format_version=int(raw["data_format_version"]),
            volume_id=str(uuid.UUID(raw["volume_id"])),
            created_at=created_at,
        )
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise VolumeValidationError(
            VolumeProblem.MARKER_INVALID, "invalid AQENO-DATA marker"
        ) from exc
    if marker.data_format_version != DATA_FORMAT_VERSION:
        raise VolumeValidationError(
            VolumeProblem.VERSION_UNSUPPORTED,
            f"data format {marker.data_format_version} is not supported",
        )
    return marker


def _validate_layout(root: Path) -> None:
    required_directories = (
        "state/config",
        "state/artwork/original",
        "state/identity",
        "state/secrets",
        "media",
        "cache/artwork",
        "cache/index",
        "tmp/imports",
        "tmp/backup",
        "tmp/restore",
        "backups",
    )
    invalid = [
        relative
        for relative in required_directories
        if (root / relative).is_symlink() or not (root / relative).is_dir()
    ]
    if invalid:
        raise VolumeValidationError(
            VolumeProblem.LAYOUT_INVALID,
            "AQENO-DATA layout is incomplete or invalid: " + ", ".join(invalid),
        )


def validate_data_volume(
    root: Path,
    *,
    require_mount: bool = True,
    mount_checker: Callable[[Path], bool] = os.path.ismount,
    writable_checker: Callable[[Path], bool] | None = None,
    usage: DiskUsage | None = None,
    require_layout: bool = True,
) -> tuple[VolumeMarker, CapacityStatus]:
    if not root.exists():
        raise VolumeValidationError(VolumeProblem.MISSING, f"AQENO-DATA is missing: {root}")
    if not root.is_dir():
        raise VolumeValidationError(VolumeProblem.MARKER_INVALID, "AQENO-DATA is not a directory")
    if require_mount and not mount_checker(root):
        raise VolumeValidationError(
            VolumeProblem.NOT_MOUNTED, f"{root} exists but is not the expected mount"
        )
    if writable_checker is None:

        def _writable(path: Path) -> bool:
            return os.access(path, os.W_OK | os.X_OK)

        writable_checker = _writable
    if not writable_checker(root):
        problem = (
            VolumeProblem.READ_ONLY if os.access(root, os.R_OK) else VolumeProblem.PERMISSION_DENIED
        )
        raise VolumeValidationError(problem, f"AQENO-DATA is not writable: {root}")
    marker = _read_marker(root)
    if require_layout:
        _validate_layout(root)
    capacity = capacity_status(root, usage=usage)
    return marker, capacity


def create_data_layout(root: Path) -> None:
    """Create the classified layout after the volume itself was validated."""
    for relative in (
        "state/config",
        "state/artwork/original",
        "state/identity",
        "state/secrets",
        "media",
        "cache/artwork",
        "cache/index",
        "tmp/imports",
        "tmp/backup",
        "tmp/restore",
        "backups",
    ):
        (root / relative).mkdir(parents=True, exist_ok=True)
    (root / "state/secrets").chmod(0o700)
