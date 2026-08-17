from __future__ import annotations

from datetime import timedelta

import pytest

from aqeno.adapters.fakes import FakeAudioEngine, FakeClock, FakeInputBus, FakeLibrary
from aqeno.application.playback import PlaybackSession, SourceResolutionRequiredError
from aqeno.config.defaults import default_settings
from aqeno.domain.content import Chapter, ContentId, ContentItem, ContentKind, HttpSource
from aqeno.domain.profile import (
    DisplayPolicy,
    ExperienceLevel,
    Profile,
    Role,
    VolumeLimits,
)
from aqeno.ports.audio import AudioCapabilities, TransportState
from aqeno.ports.input import NfcPresented, TogglePlayback, VolumeDelta


def _profile() -> Profile:
    return Profile(
        name="kids-early",
        level=ExperienceLevel.KIDS_EARLY,
        role=Role.USER,
        display=DisplayPolicy(
            inactivity_timeout=timedelta(seconds=30),
            night_timeout=timedelta(seconds=10),
            allows_dim=False,
            dim_hold=None,
            interactive_brightness=70,
            dim_brightness=0,
            ambient_brightness=40,
            night_brightness=5,
            led_brightness=20,
        ),
        volume=VolumeLimits(maximum=70, night_maximum=35, headphone_maximum=55),
    )


def _item(
    *,
    kind: ContentKind = ContentKind.AUDIOBOOK,
    duration: timedelta | None = timedelta(minutes=20),
    sources: tuple[HttpSource, ...] | None = None,
    chapters: tuple[Chapter, ...] = (),
) -> ContentItem:
    return ContentItem(
        id=ContentId(),
        title="Test item",
        kind=kind,
        sources=sources or (HttpSource("https://example.invalid/item", seekable=True),),
        chapters=chapters,
        duration=duration,
    )


class Rig:
    def __init__(self) -> None:
        self.audio = FakeAudioEngine()
        self.clock = FakeClock()
        self.inputs = FakeInputBus()
        self.library = FakeLibrary()
        self.session = PlaybackSession(
            audio=self.audio,
            library=self.library,
            clock=self.clock,
            settings=default_settings(),
            inputs=self.inputs,
        )
        self.profile = _profile()

    def start(self, item: ContentItem, *, seekable: bool = True) -> None:
        self.library.save_content(item)
        self.audio.force_next_capabilities(
            AudioCapabilities(seekable=seekable, duration=item.duration)
        )
        self.session.start(item, self.profile)


def test_start_rewinds_saved_position_and_plays() -> None:
    rig = Rig()
    item = _item()
    rig.library.save_content(item)
    rig.library.set_resume(item.id, rig.profile.name, timedelta(seconds=40))
    rig.audio.force_next_capabilities(AudioCapabilities(seekable=True, duration=item.duration))

    rig.session.start(item, rig.profile)

    assert rig.audio.state is TransportState.PLAYING
    assert rig.audio.position == timedelta(seconds=37)


def test_resume_is_shared_by_repeated_launches_of_the_content_item() -> None:
    rig = Rig()
    item = _item()
    rig.start(item)
    rig.audio.seek(timedelta(seconds=75))
    rig.session.stop()
    rig.audio.force_next_capabilities(AudioCapabilities(seekable=True, duration=item.duration))

    rig.session.start(item, rig.profile)

    assert rig.audio.position == timedelta(seconds=72)


def test_nfc_launch_uses_the_same_content_resume() -> None:
    rig = Rig()
    item = _item()
    rig.library.save_content(item)
    rig.library.map_tag("story-token", item.id)
    rig.library.set_resume(item.id, rig.profile.name, timedelta(seconds=40))
    rig.session.use_profile(rig.profile)
    rig.audio.force_next_capabilities(AudioCapabilities(seekable=True, duration=item.duration))

    rig.inputs.emit(NfcPresented("story-token"))

    assert rig.session.item == item
    assert rig.audio.position == timedelta(seconds=37)
    assert rig.audio.state is TransportState.PLAYING


def test_unassigned_tag_does_not_interrupt_playback() -> None:
    rig = Rig()
    item = _item()
    rig.start(item)
    rig.audio.seek(timedelta(seconds=18))

    rig.inputs.emit(NfcPresented("unassigned"))

    assert rig.session.item == item
    assert rig.audio.position == timedelta(seconds=18)
    assert rig.audio.state is TransportState.PLAYING


def test_short_music_restarts_instead_of_resuming() -> None:
    rig = Rig()
    item = _item(kind=ContentKind.MUSIC_TRACK, duration=timedelta(minutes=3))
    rig.library.save_content(item)
    rig.library.set_resume(item.id, rig.profile.name, timedelta(minutes=1))
    rig.audio.force_next_capabilities(AudioCapabilities(seekable=True, duration=item.duration))

    rig.session.start(item, rig.profile)

    assert rig.audio.position == timedelta(0)


def test_finished_position_starts_from_zero() -> None:
    rig = Rig()
    item = _item(duration=timedelta(minutes=10))
    rig.library.save_content(item)
    rig.library.set_resume(item.id, rig.profile.name, timedelta(minutes=9, seconds=45))
    rig.audio.force_next_capabilities(AudioCapabilities(seekable=True, duration=item.duration))

    rig.session.start(item, rig.profile)

    assert rig.audio.position == timedelta(0)


def test_playing_position_is_checkpointed_every_ten_seconds() -> None:
    rig = Rig()
    item = _item()
    rig.start(item)
    rig.audio.seek(timedelta(seconds=28))

    rig.clock.advance(timedelta(seconds=10))

    assert rig.library.get_resume(item.id, rig.profile.name) == timedelta(seconds=28)
    assert rig.clock.pending == 1


def test_pause_persists_immediately_and_stops_periodic_checkpoint() -> None:
    rig = Rig()
    item = _item()
    rig.start(item)
    rig.audio.seek(timedelta(seconds=21))

    rig.inputs.emit(TogglePlayback())

    assert rig.audio.state is TransportState.PAUSED
    assert rig.library.get_resume(item.id, rig.profile.name) == timedelta(seconds=21)
    assert rig.clock.pending == 0


def test_non_seekable_source_does_not_read_or_write_resume() -> None:
    rig = Rig()
    item = _item(duration=None)
    rig.library.save_content(item)
    rig.library.set_resume(item.id, rig.profile.name, timedelta(seconds=40))
    rig.audio.force_next_capabilities(AudioCapabilities(seekable=False, duration=None))

    rig.session.start(item, rig.profile)
    rig.clock.advance(timedelta(seconds=20))
    rig.session.stop()

    assert rig.library.get_resume(item.id, rig.profile.name) == timedelta(seconds=40)


def test_encoder_step_is_bounded_and_clamped_to_profile_ceiling() -> None:
    rig = Rig()
    item = _item()
    rig.start(item)

    rig.inputs.emit(VolumeDelta(1))
    assert rig.session.volume == 43

    rig.inputs.emit(VolumeDelta(100))
    assert rig.session.volume == 48

    for _ in range(10):
        rig.inputs.emit(VolumeDelta(100))
    assert rig.session.volume == 70
    assert rig.audio.last_volume == 70


def test_night_policy_lowers_current_volume_immediately() -> None:
    rig = Rig()
    item = _item()
    rig.start(item)
    for _ in range(5):
        rig.inputs.emit(VolumeDelta(1))

    rig.session.set_night_active(True)

    assert rig.session.volume == 35
    assert rig.audio.last_volume == 35


def test_contextual_skip_uses_long_form_steps() -> None:
    rig = Rig()
    item = _item(kind=ContentKind.AUDIOBOOK)
    rig.start(item)
    rig.audio.seek(timedelta(minutes=2))

    rig.session.next()
    assert rig.audio.position == timedelta(minutes=3)

    rig.session.previous()
    assert rig.audio.position == timedelta(minutes=2, seconds=30)


def test_embedded_chapter_controls_seek_on_the_item_timeline() -> None:
    rig = Rig()
    item = _item(
        chapters=(
            Chapter(0, "One", timedelta(0), timedelta(minutes=5)),
            Chapter(1, "Two", timedelta(minutes=5), timedelta(minutes=5)),
            Chapter(2, "Three", timedelta(minutes=10), None),
        )
    )
    rig.start(item)
    rig.audio.seek(timedelta(minutes=6))

    rig.session.next()
    assert rig.audio.position == timedelta(minutes=10)

    rig.session.previous()
    assert rig.audio.position == timedelta(minutes=5)


def test_multi_file_work_prepares_every_following_chapter() -> None:
    rig = Rig()
    sources = tuple(
        HttpSource(f"https://example.invalid/chapter-{number}", seekable=True)
        for number in range(3)
    )
    item = _item(
        sources=(sources[0],),
        chapters=tuple(
            Chapter(
                index=number,
                title=str(number),
                start=timedelta(minutes=number * 5),
                duration=timedelta(minutes=5),
                source=source,
            )
            for number, source in enumerate(sources)
        ),
        duration=timedelta(minutes=15),
    )
    rig.start(item)

    rig.audio.simulate_finished()
    assert rig.audio.state is TransportState.PLAYING
    rig.audio.simulate_finished()
    assert rig.audio.state is TransportState.PLAYING
    rig.audio.simulate_finished()

    assert rig.audio.state is TransportState.STOPPED
    assert rig.library.get_resume(item.id, rig.profile.name) == item.duration


def test_multi_file_checkpoint_uses_item_timeline() -> None:
    rig = Rig()
    first = HttpSource("https://example.invalid/one", seekable=True)
    second = HttpSource("https://example.invalid/two", seekable=True)
    item = _item(
        sources=(first,),
        chapters=(
            Chapter(0, "One", timedelta(0), timedelta(minutes=5), first),
            Chapter(1, "Two", timedelta(minutes=5), timedelta(minutes=5), second),
        ),
        duration=timedelta(minutes=10),
    )
    rig.start(item)
    rig.audio.simulate_finished()
    rig.audio.seek(timedelta(seconds=12))

    rig.clock.advance(timedelta(seconds=10))

    assert rig.library.get_resume(item.id, rig.profile.name) == timedelta(minutes=5, seconds=12)


def test_alternative_sources_require_resolution_before_playback() -> None:
    rig = Rig()
    item = _item(
        sources=(
            HttpSource("https://example.invalid/one", seekable=True),
            HttpSource("https://example.invalid/two", seekable=True),
        )
    )
    rig.library.save_content(item)

    with pytest.raises(SourceResolutionRequiredError):
        rig.session.start(item, rig.profile)
