"""Export the generated local Management API contract."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from aqeno.management.__main__ import build_app


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="aqeno-openapi-") as temporary:
        root = Path(temporary)
        os.environ.update(
            AQENO_CONFIG_DIR=str(root / "config"),
            AQENO_DATA_DIR=str(root / "data"),
            AQENO_STATE_DIR=str(root / "state"),
            AQENO_MEDIA_DIR=str(root / "media"),
            AQENO_MANAGEMENT_KEY="openapi-export-only",
        )
        schema = build_app().openapi()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
