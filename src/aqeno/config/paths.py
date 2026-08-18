"""Storage locations — ADR 0007 § 4.

XDG base directories, overridable by `AQENO_CONFIG_DIR` / `AQENO_DATA_DIR` /
`AQENO_STATE_DIR` so tests never touch real device state
(`tests/conftest.py::aqeno_state_dirs`).
"""

from __future__ import annotations

import os
from pathlib import Path


def _resolve(override_var: str, xdg_var: str, xdg_default: str) -> Path:
    override = os.environ.get(override_var)
    if override:
        # The override already names AQENO's own directory (tests point it
        # straight at a temp dir) — unlike the XDG fallback, nothing is appended.
        return Path(override)
    base = os.environ.get(xdg_var) or str(Path.home() / xdg_default)
    return Path(base) / "aqeno"


def config_dir() -> Path:
    """`settings.toml` lives here."""
    return _resolve("AQENO_CONFIG_DIR", "XDG_CONFIG_HOME", ".config")


def data_dir() -> Path:
    """`aqeno.db` lives here."""
    return _resolve("AQENO_DATA_DIR", "XDG_DATA_HOME", ".local/share")


def state_dir() -> Path:
    """Logs live here (gap G10)."""
    return _resolve("AQENO_STATE_DIR", "XDG_STATE_HOME", ".local/state")


def settings_path() -> Path:
    return config_dir() / "settings.toml"


def database_path() -> Path:
    return data_dir() / "aqeno.db"


def media_dir() -> Path:
    """Default library root — CONTENT_INGESTION.md § 1.

    `AQENO_MEDIA_DIR` overrides it directly (no `aqeno` suffix appended, same
    convention as the other `AQENO_*_DIR` overrides) so tests never touch real
    media.
    """
    override = os.environ.get("AQENO_MEDIA_DIR")
    if override:
        return Path(override)
    return data_dir() / "media"


def artwork_dir() -> Path:
    """Extracted embedded artwork lives here — CONTENT_INGESTION.md § 7."""
    return data_dir() / "artwork"
