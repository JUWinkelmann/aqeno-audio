"""TOML-backed `SettingsStore` — ADR 0007 § "Settings".

`settings.toml` is hand-editable and therefore untrusted input: `load()` never
raises. A missing file, unreadable file, unparseable TOML, or any out-of-range
or wrongly-typed value falls back to its default, is logged, and — critically —
the file on disk is left exactly as found. AQENO does not "fix" a file a Manager
is mid-edit of.

`tomllib` (stdlib, Python 3.11+) parses TOML but does not write it, so `save()`
uses a small hand-rolled serialiser restricted to the flat/nested-table shape
`config.defaults.Settings` actually has: scalars, one level of `[section]`
tables, and lists of scalars. It does not need to be a general TOML writer.
"""

from __future__ import annotations

import contextlib
import logging
import os
import tempfile
import tomllib
from dataclasses import asdict
from pathlib import Path
from typing import Any

from aqeno.config.defaults import Settings, default_settings, validate
from aqeno.config.paths import settings_path

logger = logging.getLogger(__name__)


def _format_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(value, list | tuple):
        return "[" + ", ".join(_format_value(v) for v in value) + "]"
    raise TypeError(f"cannot serialise {value!r} to TOML")  # pragma: no cover


def _dump_toml(data: dict[str, Any]) -> str:
    scalars = {k: v for k, v in data.items() if not isinstance(v, dict)}
    sections = {k: v for k, v in data.items() if isinstance(v, dict)}

    lines: list[str] = [f"{k} = {_format_value(v)}" for k, v in scalars.items()]
    if scalars and sections:
        lines.append("")

    section_items = list(sections.items())
    for i, (name, table) in enumerate(section_items):
        lines.append(f"[{name}]")
        lines.extend(f"{k} = {_format_value(v)}" for k, v in table.items())
        if i != len(section_items) - 1:
            lines.append("")

    return "\n".join(lines) + "\n"


def _atomic_write(path: Path, content: str) -> None:
    """Temp file in the same directory, fsync it, `os.replace`, fsync the
    directory. All four steps — anything less can leave a truncated file after
    power loss (ADR 0007)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp_name)
        raise

    dir_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


class TomlSettingsStore:
    """Implements `aqeno.ports.persistence.SettingsStore`."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path if path is not None else settings_path()

    def load(self) -> Settings:
        if not self._path.exists():
            return default_settings()

        try:
            raw_text = self._path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("cannot read %s (%s); starting from defaults", self._path, exc)
            return default_settings()

        try:
            raw = tomllib.loads(raw_text)
        except tomllib.TOMLDecodeError as exc:
            logger.warning(
                "%s is not valid TOML (%s); starting from defaults, file left untouched",
                self._path,
                exc,
            )
            return default_settings()

        settings, warnings = validate(raw)
        for warning in warnings:
            logger.warning("settings.toml: %s", warning)
        return settings

    def save(self, settings: Settings) -> None:
        content = _dump_toml(asdict(settings))
        _atomic_write(self._path, content)
