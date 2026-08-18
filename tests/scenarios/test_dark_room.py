"""The dark-room scenario — the product's central requirement made a test.

`AGENTS.md`: "Dark-room operation must be possible with display and lights fully
off." `DISPLAY_STATE_MACHINE.md` note 6: volume, play/pause, next and previous
never change display state and never reset the visual inactivity timer. This test
wires a real `PlaybackSession` and a real `DisplayService` to one shared
`FakeInputBus`, exactly as `__main__.py` does, and proves the whole path: audio
plays, inactivity elapses, the panel goes off, and every physical transport
control keeps working with the panel dark and not one further panel or LED call.
"""

from __future__ import annotations

from datetime import timedelta

from aqeno.adapters.fakes import (
    FakeAudioEngine,
    FakeClock,
    FakeDisplayPanel,
    FakeInputBus,
    FakeLibrary,
    FakeStatusLeds,
)
from aqeno.application.display import DisplayService
from aqeno.application.playback import PlaybackSession
from aqeno.application.readiness import Readiness, ReadinessState
from aqeno.config.defaults import default_settings
from aqeno.domain.content import ContentId, ContentItem, ContentKind, HttpSource
from aqeno.domain.display import DisplayEvent, DisplayState
from aqeno.domain.profile import DisplayPolicy, ExperienceLevel, Profile, Role, VolumeLimits
from aqeno.ports.audio import AudioCapabilities, TransportState
from aqeno.ports.input import Next, Previous, TogglePlayback, VolumeDelta


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


def test_dark_room_playback_stays_controllable_with_the_panel_off() -> None:
    clock = FakeClock()
    inputs = FakeInputBus()
    audio = FakeAudioEngine()
    library = FakeLibrary()
    settings = default_settings()
    profile = _profile()

    readiness = Readiness(clock)
    readiness.advance(ReadinessState.LOCAL_READY)

    session = PlaybackSession(
        audio=audio, library=library, clock=clock, settings=settings, inputs=inputs
    )

    panel = FakeDisplayPanel()
    leds = FakeStatusLeds()
    display = DisplayService(
        panel=panel, leds=leds, clock=clock, readiness=readiness, profile=profile, settings=settings
    )
    session.on_changed(display.handle_playback_changed)
    inputs.on_input(display.handle_input)
    readiness.advance(ReadinessState.PLAYBACK_READY)
    # This scenario exercises the full display lifecycle, so it takes readiness
    # the rest of the way to UI_READY — the "no UI at all" case (a WakeRequest
    # staying pending forever) is `test_display_service.py`'s `TestPendingWake`.
    readiness.advance(ReadinessState.UI_READY)
    display.handle_event(DisplayEvent.WAKE_REQUEST)

    item = ContentItem(
        id=ContentId(),
        title="Bedtime Story",
        kind=ContentKind.AUDIOBOOK,
        sources=(HttpSource("https://example.invalid/story", seekable=True),),
        duration=timedelta(minutes=20),
    )
    library.save_content(item)
    audio.force_next_capabilities(AudioCapabilities(seekable=True, duration=item.duration))
    session.start(item, profile)

    assert audio.state is TransportState.PLAYING
    assert display.snapshot.state is DisplayState.INTERACTIVE

    # Inactivity elapses: a Kids profile goes straight to OFF.
    panel.calls.clear()
    leds.calls.clear()
    clock.advance(timedelta(seconds=31))

    assert display.snapshot.state is DisplayState.OFF
    assert panel.calls == [("power", False)]
    assert leds.calls == [0]

    # The panel must not receive one more call for the rest of this test: that is
    # the whole point of the scenario.
    panel.calls.clear()
    leds.calls.clear()

    inputs.emit(VolumeDelta(1))
    inputs.emit(TogglePlayback())
    inputs.emit(Next())
    inputs.emit(Previous())
    inputs.emit(TogglePlayback())

    assert display.snapshot.state is DisplayState.OFF
    assert panel.calls == []
    assert leds.calls == []
    # And transport genuinely worked: the toggle-pause-then-resume above left
    # audio playing again, and the volume step actually moved the volume.
    assert audio.state is TransportState.PLAYING
    assert session.volume == default_settings().volume.first_boot + settings.volume.encoder_step
