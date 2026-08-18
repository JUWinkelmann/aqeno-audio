from __future__ import annotations

from pathlib import Path

from aqeno.__main__ import main
from aqeno.adapters.persistence import open_library


def test_local_core_starts_with_fake_hardware(aqeno_state_dirs: Path) -> None:
    assert main(["--fake-hardware", "--check"]) == 0

    library = open_library(aqeno_state_dirs / "aqeno_data_dir")
    try:
        profile = library.get_profile("kids-early")
        assert profile is not None
        assert profile.name == "kids-early"
    finally:
        library.close()


def test_unknown_profile_fails_without_creating_it(aqeno_state_dirs: Path) -> None:
    assert main(["--profile", "missing", "--fake-hardware", "--check"]) == 1

    library = open_library(aqeno_state_dirs / "aqeno_data_dir")
    try:
        assert library.get_profile("missing") is None
    finally:
        library.close()
