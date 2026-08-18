"""Contract suite for the `MediaProbe` port — ADR 0014 § 1.

`MutagenProbe` is exercised against real containers rendered with GStreamer at
test time (ADR 0008 § 7, same pattern as `tests/contracts/test_audio.py`): a
multi-file MP3 "work", a FLAC file, and an MP3 carrying real ID3 `CHAP`
chapter frames written with `mutagen` itself — the same library reads them
back, which is the honest way to prove the round trip without a second
chapter-authoring tool. `FakeMediaProbe` (tests/unit/test_ingestion.py) covers
the policy; this file covers what mutagen actually hands back from bytes on
disk.
"""

# ruff: noqa: E402 -- Gst must be version-pinned before importing gi.repository.

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import gi
import pytest

gi.require_version("Gst", "1.0")
from gi.repository import Gst

from aqeno.adapters.metadata.mutagen_probe import MutagenProbe

Gst.init(None)


_MP3_ENCODER = "lamemp3enc target=1 bitrate=128 cbr=true"
"""Forced CBR: lamemp3enc's default VBR mode writes no Xing header, so mutagen
falls back to (file size / first-frame bitrate) and gets the duration wrong by
an order of magnitude. CBR makes that estimate exact, which is what real-world
CBR rips (and mutagen against them) rely on too."""


def _render(path: Path, *, seconds: int, encoder: str, freq: int = 440) -> Path:
    description = (
        f"audiotestsrc wave=sine freq={freq} samplesperbuffer=44100 num-buffers={seconds} "
        f"! audioconvert ! audio/x-raw,rate=44100 ! {encoder} ! filesink location={path}"
    )
    pipeline = Gst.parse_launch(description)
    pipeline.set_state(Gst.State.PLAYING)
    bus = pipeline.get_bus()
    message = bus.timed_pop_filtered(15 * Gst.SECOND, Gst.MessageType.EOS | Gst.MessageType.ERROR)
    pipeline.set_state(Gst.State.NULL)
    if message is None:
        raise RuntimeError(f"timed out rendering fixture {path}")
    if message.type == Gst.MessageType.ERROR:
        raise RuntimeError(f"failed to render fixture {path}: {message.parse_error()}")
    return path


@pytest.fixture(scope="module")
def mp3_file(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("mutagen-fixtures")
    path = _render(root / "track.mp3", seconds=2, encoder=_MP3_ENCODER)

    from mutagen.easyid3 import EasyID3

    tags = EasyID3()
    tags["title"] = "Erstes Kapitel"
    tags["album"] = "Die Kuh Lieselotte"
    tags["genre"] = "Hörspiel"
    tags["tracknumber"] = "3"
    tags["language"] = "de"
    tags.save(path)
    return path


@pytest.fixture(scope="module")
def flac_file(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("mutagen-fixtures")
    path = _render(root / "track.flac", seconds=2, encoder="flacenc")

    from mutagen.flac import FLAC

    audio = FLAC(path)
    audio["title"] = "Track One"
    audio["album"] = "Sample Album"
    audio["genre"] = "Pop"
    audio["tracknumber"] = "1"
    audio["replaygain_track_gain"] = "-6.50 dB"
    audio["replaygain_track_peak"] = "0.987654"
    audio.save()
    return path


@pytest.fixture(scope="module")
def multi_file_work(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    root = tmp_path_factory.mktemp("mutagen-multi")
    a = _render(root / "a.mp3", seconds=1, encoder=_MP3_ENCODER, freq=440)
    b = _render(root / "b.mp3", seconds=1, encoder=_MP3_ENCODER, freq=880)
    return a, b


@pytest.fixture(scope="module")
def chaptered_mp3(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A real MP3 with real ID3 `CHAP` frames, written and then read back by
    `mutagen` — the CONTENT_INGESTION.md § 12 "something carrying embedded
    chapters" fixture."""
    root = tmp_path_factory.mktemp("mutagen-chapters")
    path = _render(root / "chaptered.mp3", seconds=4, encoder=_MP3_ENCODER)

    from mutagen.id3 import CHAP, CTOC, ID3, TIT2, CTOCFlags

    tags = ID3()
    tags.add(
        CHAP(
            element_id="chp1",
            start_time=0,
            end_time=2000,
            sub_frames=[TIT2(text=["Scene One"])],
        )
    )
    tags.add(
        CHAP(
            element_id="chp2",
            start_time=2000,
            end_time=4000,
            sub_frames=[TIT2(text=["Scene Two"])],
        )
    )
    tags.add(
        CTOC(
            element_id="toc",
            flags=CTOCFlags.TOP_LEVEL | CTOCFlags.ORDERED,
            child_element_ids=["chp1", "chp2"],
        )
    )
    tags.save(path)
    return path


class TestTagsAndDuration:
    def test_reads_duration_and_id3_tags_from_a_real_mp3(self, mp3_file: Path) -> None:
        probed = MutagenProbe().probe(mp3_file)
        assert probed is not None
        assert probed.duration is not None
        assert timedelta(seconds=1.5) < probed.duration < timedelta(seconds=3)
        assert probed.title == "Erstes Kapitel"
        assert probed.album == "Die Kuh Lieselotte"
        assert probed.genre == "Hörspiel"
        assert probed.track_number == 3
        assert probed.language == "de"

    def test_reads_duration_and_vorbis_comments_from_a_real_flac(self, flac_file: Path) -> None:
        probed = MutagenProbe().probe(flac_file)
        assert probed is not None
        assert probed.title == "Track One"
        assert probed.album == "Sample Album"
        assert probed.genre == "Pop"
        assert probed.track_number == 1

    def test_reads_replaygain_tags_when_present(self, flac_file: Path) -> None:
        probed = MutagenProbe().probe(flac_file)
        assert probed is not None
        assert probed.replaygain.track_gain_db == pytest.approx(-6.5)
        assert probed.replaygain.track_peak == pytest.approx(0.987654)

    def test_missing_file_returns_none_rather_than_raising(self, tmp_path: Path) -> None:
        assert MutagenProbe().probe(tmp_path / "does-not-exist.mp3") is None

    def test_a_non_audio_file_returns_none(self, tmp_path: Path) -> None:
        fake = tmp_path / "not-audio.mp3"
        fake.write_bytes(b"this is not audio, just noise" * 20)
        assert MutagenProbe().probe(fake) is None


class TestFingerprint:
    def test_fingerprint_is_stable_across_retagging(self, tmp_path: Path) -> None:
        # Well over the 64 KiB fingerprint window, so the *initial* tag write
        # (which does shift the audio start once) leaves the midpoint window
        # deep in untouched audio.
        path = _render(tmp_path / "song.mp3", seconds=10, encoder=_MP3_ENCODER)
        assert path.stat().st_size > 128 * 1024

        from mutagen.easyid3 import EasyID3

        tags = EasyID3()
        tags["title"] = "Original Title"
        tags["album"] = "Original Album"
        tags.save(path)
        before = MutagenProbe().probe(path)
        assert before is not None

        # A real retag: mutagen reuses the existing tag's padding, so the file
        # size — and therefore the fingerprint window — does not move
        # (CONTENT_INGESTION.md § 4: "the fingerprint window is audio payload,
        # not the header").
        tags_again = EasyID3(path)
        tags_again["title"] = "Corrected Title"
        tags_again.save(path)

        after = MutagenProbe().probe(path)
        assert after is not None
        assert after.fingerprint == before.fingerprint

    def test_different_files_fingerprint_differently(
        self, multi_file_work: tuple[Path, Path]
    ) -> None:
        a, b = multi_file_work
        probed_a = MutagenProbe().probe(a)
        probed_b = MutagenProbe().probe(b)
        assert probed_a is not None
        assert probed_b is not None
        assert probed_a.fingerprint != probed_b.fingerprint


class TestEmbeddedChapters:
    def test_reads_id3_chap_frames_in_order(self, chaptered_mp3: Path) -> None:
        probed = MutagenProbe().probe(chaptered_mp3)
        assert probed is not None
        assert [c.title for c in probed.chapters] == ["Scene One", "Scene Two"]
        assert probed.chapters[0].start == timedelta(0)
        assert probed.chapters[1].start == timedelta(seconds=2)
        assert probed.chapters[0].duration == timedelta(seconds=2)

    def test_a_file_without_chapters_has_none(self, mp3_file: Path) -> None:
        probed = MutagenProbe().probe(mp3_file)
        assert probed is not None
        assert probed.chapters == ()
