"""Content kind behaviour — ADR 0009."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from aqeno.domain.content import (
    Chapter,
    ContentId,
    ContentItem,
    ContentKind,
    LocalFileSource,
    TransportBehaviour,
    policy_for,
)


@pytest.mark.parametrize("kind", list(ContentKind))
def test_every_kind_has_a_policy(kind: ContentKind) -> None:
    assert policy_for(kind) is not None


class TestShuffle:
    @pytest.mark.parametrize("kind", [ContentKind.AUDIOBOOK, ContentKind.AUDIO_DRAMA])
    def test_shuffle_is_impossible_for_long_form(self, kind: ContentKind) -> None:
        """Not merely off: a control that exists will be found by a child."""
        assert policy_for(kind).shuffle_permitted is False

    def test_shuffle_is_permitted_for_music(self) -> None:
        assert policy_for(ContentKind.MUSIC_ALBUM).shuffle_permitted is True


class TestTransport:
    @pytest.mark.parametrize("kind", [ContentKind.AUDIOBOOK, ContentKind.AUDIO_DRAMA])
    def test_long_form_skips_asymmetrically(self, kind: ContentKind) -> None:
        """Recovering your place needs more context than you skipped forward."""
        policy = policy_for(kind)
        assert policy.transport is TransportBehaviour.CHAPTER_ELSE_SKIP
        assert policy.skip_forward == timedelta(seconds=60)
        assert policy.skip_back == timedelta(seconds=30)
        assert policy.skip_back is not None and policy.skip_forward is not None
        assert policy.skip_back < policy.skip_forward

    def test_radio_ignores_transport(self) -> None:
        assert policy_for(ContentKind.RADIO_STREAM).transport is TransportBehaviour.IGNORED

    def test_music_uses_the_restart_convention(self) -> None:
        assert policy_for(ContentKind.MUSIC_TRACK).restart_threshold == timedelta(seconds=3)


class TestResume:
    @pytest.mark.parametrize(
        "kind", [ContentKind.AUDIOBOOK, ContentKind.AUDIO_DRAMA, ContentKind.PODCAST_EPISODE]
    )
    def test_long_form_resumes_exactly(self, kind: ContentKind) -> None:
        assert policy_for(kind).exact_resume is True

    def test_radio_has_no_resume(self) -> None:
        assert policy_for(ContentKind.RADIO_STREAM).exact_resume is False


class TestNoAutoAdvanceIntoUnrelatedContent:
    """P12: AQENO does not optimise for engagement."""

    @pytest.mark.parametrize("kind", [ContentKind.PODCAST_EPISODE, ContentKind.RADIO_STREAM])
    def test_standalone_kinds_stop_at_the_end(self, kind: ContentKind) -> None:
        assert policy_for(kind).advance_within_collection is False


class TestMultiFileWorkIsOneItem:
    def test_forty_files_are_one_item_with_chapters(self) -> None:
        """Kids Early shows very few large tiles; forty tiles for one book would
        destroy that surface (ADR 0009 § 4)."""
        item = ContentItem(
            id=ContentId(),
            title="Die drei ???",
            kind=ContentKind.AUDIO_DRAMA,
            sources=(LocalFileSource(path=Path("/media/cd")),),
            chapters=tuple(
                Chapter(
                    index=i,
                    title=f"Track {i + 1}",
                    start=timedelta(minutes=3 * i),
                    duration=timedelta(minutes=3),
                )
                for i in range(40)
            ),
        )
        assert item.has_chapters
        assert len(item.chapters) == 40
        assert item.policy.shuffle_permitted is False
