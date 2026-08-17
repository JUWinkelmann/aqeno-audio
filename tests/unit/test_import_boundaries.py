"""The architecture boundary as a test, not as discipline.

ADR 0001 forbids framework and hardware imports in the pure layers. ADR 0010 adds two
more boundaries: nothing outside `adapters/` may reach the network, and dependencies
point inward. Python makes each violation a one-line accident, and each destroys
something the architecture exists to protect — so they are checked mechanically on
every push (ADR 0008 § 6).

A documented rule that nothing checks is a rule that erodes.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

import aqeno

SOURCE_ROOT = Path(aqeno.__file__).parent
PURE_PACKAGES = ("domain", "application", "ports", "config")
"""`config/` is in here because `ports/` imports it: without it the guard has a hole."""

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

NETWORK_MODULES = frozenset(
    {
        "socket",
        "socketserver",
        "ssl",
        "http",
        "urllib",
        "urllib3",
        "ftplib",
        "smtplib",
        "poplib",
        "imaplib",
        "xmlrpc",
        "requests",
        "httpx",
        "aiohttp",
        "websockets",
    }
)
"""ADR 0010 § 4. Only `adapters/` may reach the network.

This is what turns "no artificial SaaS dependency" from a promise into an invariant.
A port may *describe* network state as a Protocol — describing it needs no socket.
"""

LAYER_RULES: dict[str, tuple[str, ...]] = {
    "domain": ("aqeno.application", "aqeno.ports", "aqeno.adapters", "aqeno.ui", "aqeno.config"),
    "application": ("aqeno.adapters", "aqeno.ui"),
    "ports": ("aqeno.adapters", "aqeno.ui"),
    "config": ("aqeno.adapters", "aqeno.ui"),
    "adapters": ("aqeno.ui",),
    "ui": ("aqeno.adapters",),
}
"""Which `aqeno.*` packages each layer may NOT import. Dependencies point inward.

`ui` may not touch `adapters`: the UI calls application services, which is what keeps a
future service layer possible without building one today (ADR 0010 § 2 alternatives).
"""


def _modules_in(package: str) -> list[Path]:
    directory = SOURCE_ROOT / package
    if not directory.exists():
        return []
    return sorted(directory.rglob("*.py"))


def _pure_modules() -> list[Path]:
    modules: list[Path] = []
    for package in PURE_PACKAGES:
        modules.extend(_modules_in(package))
    return modules


def _non_adapter_modules() -> list[Path]:
    return [
        path
        for path in sorted(SOURCE_ROOT.rglob("*.py"))
        if not path.is_relative_to(SOURCE_ROOT / "adapters")
    ]


def _layer_modules() -> list[tuple[str, Path]]:
    return [(layer, module) for layer in LAYER_RULES for module in _modules_in(layer)]


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


@pytest.mark.parametrize("module", _non_adapter_modules(), ids=_module_id)
def test_only_adapters_reach_the_network(module: Path) -> None:
    """ADR 0010 § 4. No function is routed through a server because it might one day
    become a subscription. Enforced, not promised."""
    tree = ast.parse(module.read_text(encoding="utf-8"))
    for root in _imported_roots(tree):
        assert root not in NETWORK_MODULES, (
            f"{_module_id(module)} imports {root!r}. Only adapters/ may reach the "
            f"network — the Core must stay fully functional with no network at all "
            f"(ADR 0010 § 1)."
        )


@pytest.mark.parametrize(
    "layer,module",
    _layer_modules(),
    ids=lambda param: _module_id(param) if isinstance(param, Path) else str(param),
)
def test_dependencies_point_inward(layer: str, module: Path) -> None:
    forbidden = LAYER_RULES[layer]
    tree = ast.parse(module.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith(forbidden), (
                f"{_module_id(module)} imports {node.module!r}, which {layer}/ may not. "
                f"Dependencies point inward (ADR 0010 § 4, DEVELOPMENT.md)."
            )


def test_the_check_actually_covers_something() -> None:
    """A boundary test that silently matches no files is worse than none."""
    assert len(_pure_modules()) >= 3
    assert len(_non_adapter_modules()) >= 3
    assert len(_layer_modules()) >= 3
