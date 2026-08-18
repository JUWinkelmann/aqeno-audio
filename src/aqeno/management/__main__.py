from __future__ import annotations

import argparse

import uvicorn
from fastapi import FastAPI

from aqeno.adapters.fakes.input import FakeInputBus
from aqeno.adapters.persistence.sqlite_library import open_library
from aqeno.adapters.persistence.toml_settings import TomlSettingsStore
from aqeno.appliance.storage import validate_data_volume
from aqeno.config.paths import appliance_mode, paths
from aqeno.management.api import create_app
from aqeno.management.runtime import build_context


def build_app() -> FastAPI:
    if appliance_mode():
        validate_data_volume(paths().data_root)
    library = open_library()
    settings_store = TomlSettingsStore()
    inputs = FakeInputBus()
    context = build_context(
        library=library,
        settings_store=settings_store,
        inputs=inputs,
    )
    return create_app(context)


def main() -> int:
    parser = argparse.ArgumentParser(description="AQENO Local Management API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8766, type=int)
    args = parser.parse_args()
    uvicorn.run(build_app(), host=args.host, port=args.port, access_log=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
