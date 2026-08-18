from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_committed_openapi_matches_generated_contract(tmp_path: Path) -> None:
    generated = tmp_path / "openapi.json"
    subprocess.run(
        [sys.executable, "scripts/export_management_openapi.py", str(generated)],
        cwd=ROOT,
        check=True,
    )
    assert generated.read_bytes() == (ROOT / "docs/management/openapi.json").read_bytes()
