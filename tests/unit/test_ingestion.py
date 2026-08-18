"""Ingestion policy — CONTENT_INGESTION.md §§ 2-8, 13.

Pure application-layer tests: real directories and empty files on disk (so
`pathlib` walking behaves like it will in production), but metadata comes from
`FakeMediaProbe` so the whole policy is testable without real audio containers.
Real-container fixtures live in `tests/contracts/test_mutagen_probe.py`.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from aqeno.adapters.fakes.clock import FakeClock
from aqeno.adapters.fakes.metadata import FakeMediaProbe
from aqeno.adapters.fakes.persistence import FakeLibrary
from aqeno.application.ingestion import (
    ScanSummary,
    build_chapters,
    infer_kind,
    natural_sort_key,
    run_scan,
)
from aqeno.domain.content import ContentKind, Fingerprint
from aqeno.ports.media_probe import ProbedChapter, ProbedFile
from aqeno.ports.persistence import DatabaseHealth


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x00" * 100)
    return path


def _fingerprint(tag: str) -> Fingerprint:
    return Fingerprint(size_bytes=100, digest=tag.encode().ljust(16, b"\x00"))


def _probed(
    path: Path,
    *,
    duration: timedelta | None = timedelta(minutes=5),
    fingerprint: Fingerprint | None = None,
    title: str | None = None,
    album: str | None = None,
    genre: str | None = None,
    track_number: int | None = None,
    language: str | None = None,
    chapters: tuple[ProbedChapter, ...] = (),
) -> ProbedFile:
    return ProbedFile(
        path=path,
        size_bytes=100,
        mtime=0.0,
        fingerprint=fingerprint if fingerprint is not None else _fingerprint(str(path)),
        duration=duration,
        title=title,
        album=album,
        genre=genre,
        track_number=track_number,
        language=language,
        chapters=chapters,
    )


def _scan(
    tmp_path: Path, probe: FakeMediaProbe, library: FakeLibrary, clock: FakeClock
) -> ScanSummary:
    return run_scan(
        library=library,
        probe=probe,
        clock=clock,
        roots=(tmp_path,),
        follow_symlinks=False,
        artwork_dir=tmp_path / "artwork",
    )


class TestIdentitySurvivesReorganisation:
    """Invariants 1-3 of CONTENT_INGESTION.md § 13."""

    def test_moving_a_works_folder_preserves_content_id_resume_and_tag_mapping(
        self, tmp_path: Path
    ) -> None:
        library = FakeLibrary()
        clock = FakeClock()
        probe = FakeMediaProbe()

        old_dir = tmp_path / "Old Name"
        file_a = _touch(old_dir / "a.mp3")
        file_b = _touch(old_dir / "b.mp3")
        probe.add(_probed(file_a, fingerprint=_fingerprint("a"), track_number=1))
        probe.add(_probed(file_b, fingerprint=_fingerprint("b"), track_number=2))

        _scan(tmp_path, probe, library, clock)
        [item] = library.list_content()
        library.map_tag("uid-1", item.id)
        library.set_resume(item.id, "kids-early", timedelta(minutes=2))

        file_a.unlink()
        file_b.unlink()
        old_dir.rmdir()
        new_dir = tmp_path / "New Name"
        new_a = _touch(new_dir / "a.mp3")
        new_b = _touch(new_dir / "b.mp3")
        probe.add(_probed(new_a, fingerprint=_fingerprint("a"), track_number=1))
        probe.add(_probed(new_b, fingerprint=_fingerprint("b"), track_number=2))

        _scan(tmp_path, probe, library, clock)

        [moved] = library.list_content()
        assert moved.id == item.id
        assert library.resolve_tag("uid-1") == item.id
        assert library.get_resume(item.id, "kids-early") == timedelta(minutes=2)

    def test_retagging_every_member_file_preserves_content_id(self, tmp_path: Path) -> None:
        library = FakeLibrary()
        clock = FakeClock()
        probe = FakeMediaProbe()

        directory = tmp_path / "Work"
        file_a = _touch(directory / "a.mp3")
        file_b = _touch(directory / "b.mp3")
        probe.add(_probed(file_a, fingerprint=_fingerprint("a"), track_number=1, title="Old"))
        probe.add(_probed(file_b, fingerprint=_fingerprint("b"), track_number=2, title="Old"))
        _scan(tmp_path, probe, library, clock)
        [item] = library.list_content()

        probe.add(_probed(file_a, fingerprint=_fingerprint("a"), track_number=1, title="New"))
        probe.add(_probed(file_b, fingerprint=_fingerprint("b"), track_number=2, title="New"))
        _scan(tmp_path, probe, library, clock)

        [rescanned] = library.list_content()
        assert rescanned.id == item.id

    def test_replacing_a_minority_of_files_preserves_identity(self, tmp_path: Path) -> None:
        library = FakeLibrary()
        clock = FakeClock()
        probe = FakeMediaProbe()

        directory = tmp_path / "Work"
        files = [_touch(directory / f"{i}.mp3") for i in range(3)]
        for i, f in enumerate(files):
            probe.add(_probed(f, fingerprint=_fingerprint(f"orig-{i}"), track_number=i))
        _scan(tmp_path, probe, library, clock)
        [item] = library.list_content()

        # Replace one of three files (a minority) with a re-encode: new fingerprint.
        probe.add(_probed(files[0], fingerprint=_fingerprint("reencoded"), track_number=0))
        _scan(tmp_path, probe, library, clock)

        [rescanned] = library.list_content()
        assert rescanned.id == item.id

    def test_replacing_every_file_creates_a_new_item_and_the_old_one_becomes_unavailable(
        self, tmp_path: Path
    ) -> None:
        library = FakeLibrary()
        clock = FakeClock()
        probe = FakeMediaProbe()

        directory = tmp_path / "Work"
        files = [_touch(directory / f"{i}.mp3") for i in range(3)]
        for i, f in enumerate(files):
            probe.add(_probed(f, fingerprint=_fingerprint(f"orig-{i}"), track_number=i))
        _scan(tmp_path, probe, library, clock)
        [original] = library.list_content()

        for i, f in enumerate(files):
            probe.add(_probed(f, fingerprint=_fingerprint(f"reencoded-{i}"), track_number=i))
        _scan(tmp_path, probe, library, clock)

        items = library.list_content()
        assert len(items) == 2
        by_id = {item.id: item for item in items}
        assert by_id[original.id].available is False
        new_item = next(item for item in items if item.id != original.id)
        assert new_item.available is True


class TestChapters:
    def test_a_folder_of_forty_files_is_one_item_with_forty_chapters_and_strictly_increasing_starts(
        self, tmp_path: Path
    ) -> None:
        library = FakeLibrary()
        clock = FakeClock()
        probe = FakeMediaProbe()

        directory = tmp_path / "Big Work"
        for i in range(40):
            f = _touch(directory / f"track-{i:02d}.mp3")
            probe.add(_probed(f, fingerprint=_fingerprint(f"t{i}"), track_number=i))

        _scan(tmp_path, probe, library, clock)

        [item] = library.list_content()
        assert len(item.chapters) == 40
        starts = [c.start for c in item.chapters]
        assert starts == sorted(starts)
        assert len(set(starts)) == 40  # strictly increasing

    def test_kapitel_10_sorts_after_kapitel_2(self, tmp_path: Path) -> None:
        directory = tmp_path / "Work"
        f2 = _touch(directory / "Kapitel 2.mp3")
        f10 = _touch(directory / "Kapitel 10.mp3")
        probes = {
            f2: _probed(f2, fingerprint=_fingerprint("2")),
            f10: _probed(f10, fingerprint=_fingerprint("10")),
        }
        # No track numbers and no playlist: falls through to natural filename order.
        chapters = build_chapters(directory, [f10, f2], probes)
        assert [c.source.path.name for c in chapters if c.source] == [
            "Kapitel 2.mp3",
            "Kapitel 10.mp3",
        ]

    def test_natural_sort_key_orders_digit_runs_numerically(self) -> None:
        names = ["Kapitel 10", "Kapitel 2", "Kapitel 1"]
        assert sorted(names, key=natural_sort_key) == ["Kapitel 1", "Kapitel 2", "Kapitel 10"]


class TestKindInference:
    """CONTENT_INGESTION.md § 5 — one case per rule, table-driven."""

    def test_a_work_with_no_kind_signal_is_ingested_as_audio_drama(self, tmp_path: Path) -> None:
        library = FakeLibrary()
        clock = FakeClock()
        probe = FakeMediaProbe()
        f = _touch(tmp_path / "Work" / "only.mp3")
        probe.add(_probed(f, fingerprint=_fingerprint("x"), duration=timedelta(minutes=45)))

        _scan(tmp_path, probe, library, clock)

        [item] = library.list_content()
        assert item.kind is ContentKind.AUDIO_DRAMA
        assert item.kind_inference_rule == "8-ambiguity-default"

    @pytest.mark.parametrize(
        ("probes_kwargs", "chapters_kwargs", "expected_kind", "expected_rule"),
        [
            pytest.param(
                [{"path_suffix": "book.m4b"}],
                [{}],
                ContentKind.AUDIOBOOK,
                "3-m4b-extension",
                id="rule-3-m4b-extension",
            ),
            pytest.param(
                [{"genre": "Hörbuch"}],
                [{}],
                ContentKind.AUDIOBOOK,
                "4-audiobook-keyword",
                id="rule-4-audiobook-keyword",
            ),
            pytest.param(
                [{"genre": "Kinder-Hörspiel"}],
                [{}],
                ContentKind.AUDIO_DRAMA,
                "5-drama-keyword",
                id="rule-5-drama-keyword-casefolded-substring",
            ),
            pytest.param(
                [{"genre": "Pop"}] * 5,
                [{"duration": timedelta(minutes=3)}] * 5,
                ContentKind.MUSIC_ALBUM,
                "6-music-genre-and-shape",
                id="rule-6-music-genre-and-shape",
            ),
            pytest.param(
                [{}],
                [{"duration": timedelta(minutes=4)}],
                ContentKind.MUSIC_TRACK,
                "7-short-single-file",
                id="rule-7-short-single-file",
            ),
            pytest.param(
                [{}],
                [{"duration": timedelta(hours=6)}],
                ContentKind.AUDIO_DRAMA,
                "8-ambiguity-default",
                id="rule-8-ambiguity-default-long-file",
            ),
        ],
    )
    def test_kind_inference_table(
        self,
        probes_kwargs: list[dict[str, object]],
        chapters_kwargs: list[dict[str, object]],
        expected_kind: ContentKind,
        expected_rule: str,
    ) -> None:
        from aqeno.domain.content import Chapter, LocalFileSource

        genre = probes_kwargs[0].get("genre") if probes_kwargs else None
        probes = [
            ProbedFile(
                path=Path(f"/media/f{i}{kw.get('path_suffix', '.mp3')}"),
                size_bytes=100,
                mtime=0.0,
                fingerprint=_fingerprint(f"p{i}"),
                duration=timedelta(minutes=5),
                genre=genre,
            )
            for i, kw in enumerate(probes_kwargs)
        ]
        chapters = tuple(
            Chapter(
                index=i,
                title=None,
                start=timedelta(0),
                duration=kw.get("duration", timedelta(minutes=5)),  # type: ignore[arg-type]
                source=LocalFileSource(path=Path(f"/media/f{i}.mp3")),
            )
            for i, kw in enumerate(chapters_kwargs)
        )

        kind, rule = infer_kind(
            existing=None, sidecar=_no_sidecar(), probes=probes, chapters=chapters
        )

        assert kind is expected_kind
        assert rule == expected_rule

    def test_a_manager_override_survives_a_rescan_and_is_never_re_inferred(
        self, tmp_path: Path
    ) -> None:
        library = FakeLibrary()
        clock = FakeClock()
        probe = FakeMediaProbe()
        directory = tmp_path / "Work"
        f = _touch(directory / "only.mp3")
        probe.add(_probed(f, fingerprint=_fingerprint("x"), duration=timedelta(hours=6)))

        _scan(tmp_path, probe, library, clock)
        [item] = library.list_content()
        assert item.kind is ContentKind.AUDIO_DRAMA  # rule 8, before any override

        from dataclasses import replace

        overridden = replace(item, kind=ContentKind.MUSIC_ALBUM, kind_overridden=True)
        library.save_content(overridden)

        _scan(tmp_path, probe, library, clock)

        [rescanned] = library.list_content()
        assert rescanned.kind is ContentKind.MUSIC_ALBUM
        assert rescanned.kind_overridden is True
        assert rescanned.kind_inference_rule == "1-manager-override"


def _no_sidecar() -> object:
    from aqeno.application.ingestion import _Sidecar

    return _Sidecar()


class TestFailuresDuringAScan:
    def test_an_unreadable_file_is_excluded_without_failing_the_scan_or_other_works(
        self, tmp_path: Path
    ) -> None:
        library = FakeLibrary()
        clock = FakeClock()
        probe = FakeMediaProbe()

        good_dir = tmp_path / "Good"
        good_file = _touch(good_dir / "only.mp3")
        probe.add(_probed(good_file, fingerprint=_fingerprint("good")))

        bad_dir = tmp_path / "Bad"
        _touch(bad_dir / "broken.mp3")  # never registered with the probe -> None

        summary = _scan(tmp_path, probe, library, clock)

        assert summary.candidates_seen == 2
        titles = {item.title for item in library.list_content()}
        assert "Good" in titles
        assert len(library.list_content()) == 1

    def test_a_scan_interrupted_between_two_works_leaves_a_consistent_smaller_library(
        self, tmp_path: Path
    ) -> None:
        library = FakeLibrary()
        clock = FakeClock()
        probe = FakeMediaProbe()

        first = _touch(tmp_path / "A Work" / "only.mp3")
        second = _touch(tmp_path / "B Work" / "only.mp3")
        probe.add(_probed(first, fingerprint=_fingerprint("first")))
        probe.add(_probed(second, fingerprint=_fingerprint("second")))

        original_save = library.save_content
        calls = {"count": 0}

        def failing_save(*args: object, **kwargs: object) -> None:
            calls["count"] += 1
            if calls["count"] == 2:
                raise RuntimeError("power cut")
            original_save(*args, **kwargs)  # type: ignore[arg-type]

        library.save_content = failing_save  # type: ignore[method-assign]

        with pytest.raises(RuntimeError):
            _scan(tmp_path, probe, library, clock)

        library.save_content = original_save  # type: ignore[method-assign]
        assert len(library.list_content()) == 1

    def test_a_read_only_filesystem_produces_a_scan_that_plays_but_does_not_persist(
        self, tmp_path: Path
    ) -> None:
        library = FakeLibrary(health=DatabaseHealth.DEGRADED_READ_ONLY)
        clock = FakeClock()
        probe = FakeMediaProbe()
        f = _touch(tmp_path / "Work" / "only.mp3")
        probe.add(_probed(f, fingerprint=_fingerprint("x")))

        _scan(tmp_path, probe, library, clock)  # must not raise

        assert library.list_content() == ()
