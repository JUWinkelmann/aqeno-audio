"""Canonical AQENO paths for development and appliance operation.

Desktop development keeps the XDG/explicit override behavior from ADR 0007.
Appliance operation is deliberately stricter: every persistent or disposable
AQENO path is derived from one validated data root.  It must never fall back to
HOME, /etc or /var when the data volume is absent (ADR 0020).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

APPLIANCE_ROOT = Path("/aqeno-data")
APPLICATION_ROOT = Path("/opt/aqeno")


class AppliancePathError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class AqenoPaths:
    appliance: bool
    application_root: Path
    data_root: Path
    config: Path
    database: Path
    state: Path
    media: Path
    original_artwork: Path
    derived_artwork: Path
    cache: Path
    temporary: Path
    import_staging: Path
    backup_staging: Path
    backups: Path


def _resolve(override_var: str, xdg_var: str, xdg_default: str) -> Path:
    override = os.environ.get(override_var)
    if override:
        return Path(override)
    base = os.environ.get(xdg_var) or str(Path.home() / xdg_default)
    return Path(base) / "aqeno"


def appliance_mode() -> bool:
    return os.environ.get("AQENO_APPLIANCE", "").lower() in {"1", "true", "yes"}


def paths() -> AqenoPaths:
    if appliance_mode():
        forbidden = [
            name
            for name in ("AQENO_CONFIG_DIR", "AQENO_DATA_DIR", "AQENO_STATE_DIR", "AQENO_MEDIA_DIR")
            if os.environ.get(name)
        ]
        if forbidden:
            raise AppliancePathError(
                "appliance paths derive only from AQENO_DATA_ROOT; remove " + ", ".join(forbidden)
            )
        root = Path(os.environ.get("AQENO_DATA_ROOT", APPLIANCE_ROOT))
        state = root / "state"
        return AqenoPaths(
            appliance=True,
            application_root=Path(os.environ.get("AQENO_APPLICATION_ROOT", APPLICATION_ROOT)),
            data_root=root,
            config=state / "config",
            database=state / "aqeno.db",
            state=state,
            media=root / "media",
            original_artwork=state / "artwork" / "original",
            derived_artwork=root / "cache" / "artwork",
            cache=root / "cache",
            temporary=root / "tmp",
            import_staging=root / "tmp" / "imports",
            backup_staging=root / "tmp" / "backup",
            backups=root / "backups",
        )

    config = _resolve("AQENO_CONFIG_DIR", "XDG_CONFIG_HOME", ".config")
    data = _resolve("AQENO_DATA_DIR", "XDG_DATA_HOME", ".local/share")
    state = _resolve("AQENO_STATE_DIR", "XDG_STATE_HOME", ".local/state")
    media = (
        Path(os.environ["AQENO_MEDIA_DIR"]) if os.environ.get("AQENO_MEDIA_DIR") else data / "media"
    )
    return AqenoPaths(
        appliance=False,
        application_root=Path.cwd(),
        data_root=data,
        config=config,
        database=data / "aqeno.db",
        state=state,
        media=media,
        original_artwork=data / "artwork",
        derived_artwork=data / "artwork",
        cache=data / "cache",
        temporary=data / "tmp",
        import_staging=data / "tmp" / "imports",
        backup_staging=data / "tmp" / "backup",
        backups=data / "backups",
    )


def config_dir() -> Path:
    return paths().config


def data_dir() -> Path:
    """Directory containing the database (legacy public helper)."""
    return paths().database.parent


def state_dir() -> Path:
    return paths().state


def settings_path() -> Path:
    return paths().config / "settings.toml"


def database_path() -> Path:
    return paths().database


def media_dir() -> Path:
    return paths().media


def artwork_dir() -> Path:
    """Original/custom artwork. Kept for Management API compatibility."""
    return paths().original_artwork


def derived_artwork_dir() -> Path:
    return paths().derived_artwork


def admin_credential_path() -> Path:
    return paths().state / "secrets" / "admin-auth.json"
