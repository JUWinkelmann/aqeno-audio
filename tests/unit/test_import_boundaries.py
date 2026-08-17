"""The architecture boundary as a test, not as discipline.

ADR 0001 forbids framework and hardware imports in `domain/`, `application/` and
`ports/`. Python makes that violation a one-line accident, and the violation destroys
the hardware independence the whole architecture exists to protect — so it is checked
mechanically on every push (ADR 0008 § 6).
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

import aqeno

SOURCE_ROOT = Path(aqeno.__file__).parent
PURE_PACKAGES = ("domain", "application", "ports")

FORBIDDEN_PREFIXES = (
    "PySide6",
    "PyQt5",
    "PyQt6",
    "shiboken6",
    "gi",
    "gst",
    "RPi",
    "board",
    "busio",
    "digitalio",
    "adafruit",
    "smbus",
    "smbus2",
    "serial",
)
"""Qt, GStreamer and every hardware library. Not exhaustive, and does not need to be:
the stdlib check below catches anything new."""

ALLOWED_INTERNAL = "aqeno."


def _pure_modules() -> list[Path]:
    modules: list[Path] = []
    for package in PURE_PACKAGES:
        modules.extend(sorted((SOURCE_ROOT / package).rglob("*.py")))
    return modules


def _imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative import, stays inside the package
                continue
            if node.module:
                roots.add(node.module.split(".")[0])
    return roots


def _module_id(path: Path) -> str:
    return str(path.relative_to(SOURCE_ROOT))


@pytest.mark.parametrize("module", _pure_modules(), ids=_module_id)
def test_no_forbidden_imports(module: Path) -> None:
    tree = ast.parse(module.read_text(encoding="utf-8"))
    for root in _imported_roots(tree):
        assert not root.startswith(FORBIDDEN_PREFIXES), (
            f"{_module_id(module)} imports {root!r}. Qt, GStreamer and hardware "
            f"libraries belong in adapters/ (ADR 0001)."
        )


@pytest.mark.parametrize("module", _pure_modules(), ids=_module_id)
def test_only_stdlib_and_aqeno(module: Path) -> None:
    """The stronger rule, and the one that catches dependencies nobody thought of."""
    tree = ast.parse(module.read_text(encoding="utf-8"))
    for root in _imported_roots(tree):
        if root == "aqeno" or root in sys.stdlib_module_names:
            continue
        pytest.fail(
            f"{_module_id(module)} imports {root!r}, which is neither the standard "
            f"library nor AQENO. Pure layers take no third-party dependency."
        )


def test_pure_layers_do_not_import_adapters_or_ui() -> None:
    for module in _pure_modules():
        tree = ast.parse(module.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith(("aqeno.adapters", "aqeno.ui")), (
                    f"{_module_id(module)} imports {node.module!r}. Dependencies point "
                    f"inward: adapters and UI depend on the domain, never the reverse."
                )


def test_the_check_actually_covers_something() -> None:
    """A boundary test that silently matches no files is worse than none."""
    assert len(_pure_modules()) >= 3
