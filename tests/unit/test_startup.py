from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from aqeno.__main__ import _open_process, main
from aqeno.adapters.persistence import open_library
from aqeno.domain.content import ContentId, ContentItem, ContentKind, HttpSource
from aqeno.ports.audio import TransportState


def test_local_core_starts_with_fake_hardware(aqeno_state_dirs: Path) -> None:
    assert main(["--fake-hardware", "--check"]) == 0

    library = open_library(aqeno_state_dirs / "aqeno_data_dir")
    try:
        profile = library.get_profile("kids-early")
        assert profile is not None
        assert profile.name == "kids-early"
    finally:
        library.close()


def test_local_core_starts_headless(aqeno_state_dirs: Path) -> None:
    assert main(["--fake-hardware", "audio,input", "--check"]) == 0


def test_headless_core_plays_audio(aqeno_state_dirs: Path) -> None:
    process = _open_process(profile_name="kids-early", fake_hardware=frozenset({"audio", "input"}))
    try:
        profile = process.library.get_profile("kids-early")
        assert profile is not None
        item = ContentItem(
            id=ContentId(),
            title="Headless story",
            kind=ContentKind.AUDIOBOOK,
            sources=(HttpSource("https://example.invalid/story", seekable=True),),
            duration=timedelta(minutes=5),
        )
        process.library.save_content(item)

        process.session.start(item, profile)

        assert process.session.snapshot.transport is TransportState.PLAYING
    finally:
        process.close()


def test_unknown_profile_fails_without_creating_it(aqeno_state_dirs: Path) -> None:
    assert main(["--profile", "missing", "--fake-hardware", "--check"]) == 1

    library = open_library(aqeno_state_dirs / "aqeno_data_dir")
    try:
        assert library.get_profile("missing") is None
    finally:
        library.close()
