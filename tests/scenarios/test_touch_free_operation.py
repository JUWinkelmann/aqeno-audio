"""The touch-free acceptance scenario — ADR 0024 § 6, ADR 0026 § 2.

`docs/hardware/RH1_VALIDATION_CHECKLIST.md` § Touch-free operation describes the
physical form of this test; it cannot run on the assembled box until a SELECT
control exists there. This is its automated form: the whole everyday journey is
driven through the keyboard simulator's navigation keys, which stand in for the
SELECT encoder and the HOME key, and the panel's touch listener is never called
even once.

Administration is deliberately out of scope: it belongs to the web client.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from aqeno.adapters.fakes import (
    FakeAudioEngine,
    FakeClock,
    FakeDisplayPanel,
    FakeLibrary,
    FakeStatusLeds,
)
from aqeno.adapters.input import KeyboardSimulator
from aqeno.application.device_ui import DeviceSurface, DeviceUiState
from aqeno.application.display import DisplayService
from aqeno.application.playback import PlaybackSession
from aqeno.application.readiness import Readiness, ReadinessState
from aqeno.config.defaults import default_settings
from aqeno.domain.content import ContentId, ContentItem, ContentKind, LocalFileSource
from aqeno.domain.display import DisplayState
from aqeno.domain.profile import DisplayPolicy, ExperienceLevel, Profile, Role, VolumeLimits
from aqeno.ports.audio import TransportState


def _profile() -> Profile:
    return Profile(
        name="kids-early",
        level=ExperienceLevel.KIDS_EARLY,
        role=Role.USER,
        display=DisplayPolicy(
            inactivity_timeout=timedelta(seconds=30),
            night_timeout=timedelta(seconds=10),
            allows_dim=True,
            dim_hold=timedelta(seconds=10),
            interactive_brightness=70,
            dim_brightness=8,
            ambient_brightness=40,
            night_brightness=5,
            led_brightness=20,
        ),
        volume=VolumeLimits(maximum=70, night_maximum=35, headphone_maximum=55),
    )


def _local_item(tmp_path: Path, title: str) -> ContentItem:
    source = tmp_path / f"{title.lower()}.wav"
    source.write_bytes(b"RIFF" + b"\x00" * 32)
    return ContentItem(
        id=ContentId(),
        title=title,
        kind=ContentKind.AUDIOBOOK,
        sources=(LocalFileSource(source),),
        duration=timedelta(minutes=5),
        artwork=source.with_suffix(".jpg"),
    )


def _core(
    tmp_path: Path,
) -> tuple[
    KeyboardSimulator,
    DeviceUiState,
    PlaybackSession,
    DisplayService,
    FakeDisplayPanel,
    list[int],
]:
    library = FakeLibrary()
    for title in ("Alpha", "Beta", "Gamma"):
        library.save_content(_local_item(tmp_path, title))

    clock = FakeClock()
    simulator = KeyboardSimulator()
    profile = _profile()
    session = PlaybackSession(
        audio=FakeAudioEngine(),
        library=library,
        clock=clock,
        settings=default_settings(),
        inputs=simulator,
    )
    session.use_profile(profile)

    readiness = Readiness(clock)
    readiness.advance(ReadinessState.LOCAL_READY)
    readiness.advance(ReadinessState.PLAYBACK_READY)
    readiness.advance(ReadinessState.UI_READY)

    panel = FakeDisplayPanel()
    display = DisplayService(
        panel=panel,
        leds=FakeStatusLeds(),
        clock=clock,
        readiness=readiness,
        profile=profile,
        settings=default_settings(),
    )
    session.on_changed(display.handle_playback_changed)
    simulator.on_input(display.handle_input)
    ui = DeviceUiState(library=library, playback=session, display=display, profile=profile)
    display.on_navigation(ui.handle_navigation)

    # The probe for "nobody touched the screen". Registering it on the service is
    # what makes the assertion able to fail: the same listener records a real
    # touch at the end of the journey test.
    touches: list[int] = []
    display.on_touch(lambda: touches.append(1))

    ui.refresh_library()
    return simulator, ui, session, display, panel, touches


def test_the_everyday_journey_needs_no_touch(tmp_path: Path) -> None:
    simulator, ui, session, display, panel, touches = _core(tmp_path)

    # The device starts dark. The first navigation input only wakes it.
    assert display.snapshot.state is DisplayState.OFF
    assert simulator.handle_key("d")
    assert display.snapshot.state is DisplayState.INTERACTIVE
    assert ui.snapshot.surface is DeviceSurface.HOME
    assert ui.snapshot.focused_content_id == ui.snapshot.tiles[0].content_id

    # Choose the second item and start it.
    assert simulator.handle_key("d")
    chosen = ui.snapshot.focused_content_id
    assert chosen == ui.snapshot.tiles[1].content_id
    assert simulator.handle_key("s")

    assert ui.snapshot.surface is DeviceSurface.NOW_PLAYING
    assert session.snapshot.content_id == chosen
    assert session.snapshot.transport is TransportState.PLAYING

    # Transport and volume, unchanged and still physical.
    assert simulator.handle_key("space")
    assert session.snapshot.transport is TransportState.PAUSED
    assert simulator.handle_key("space")
    assert session.snapshot.transport is TransportState.PLAYING

    before = session.snapshot.volume
    assert simulator.handle_key("up")
    assert session.snapshot.volume > before
    assert simulator.handle_key("down")

    assert simulator.handle_key("right")
    assert simulator.handle_key("left")
    assert session.snapshot.content_id == chosen

    # Home, then into another item, all without the screen.
    assert simulator.handle_key("h")
    assert ui.snapshot.surface is DeviceSurface.HOME
    assert session.snapshot.transport is TransportState.PLAYING

    assert simulator.handle_key("a")
    assert simulator.handle_key("s")
    assert ui.snapshot.surface is DeviceSurface.NOW_PLAYING

    assert touches == []

    # And the probe is not vacuous: a real touch does reach the UI.
    panel.simulate_touch()
    assert touches == [1]


def test_the_navigation_that_wakes_starts_nothing(tmp_path: Path) -> None:
    """Note 15. Pressing NAV on a dark device must not launch whatever happened
    to be focused — the person cannot see what they would be starting."""
    simulator, ui, session, display, _, _ = _core(tmp_path)
    assert display.snapshot.state is DisplayState.OFF

    assert simulator.handle_key("s")

    assert display.snapshot.state is DisplayState.INTERACTIVE
    assert session.snapshot.content_id is None
    assert ui.snapshot.surface is DeviceSurface.HOME


def test_navigation_keeps_the_dark_room_dark_for_transport(tmp_path: Path) -> None:
    """Group G exists; Group B is unchanged. Volume at 3 a.m. still wakes nothing."""
    simulator, _, session, display, _, _ = _core(tmp_path)
    simulator.handle_key("d")
    simulator.handle_key("s")
    display.set_night_active(True)
    assert display.snapshot.state is DisplayState.OFF

    assert simulator.handle_key("down")
    assert simulator.handle_key("space")

    assert display.snapshot.state is DisplayState.OFF
    assert session.snapshot.transport is TransportState.PAUSED


def test_home_wakes_and_acts_in_the_same_press(tmp_path: Path) -> None:
    """Note 17 / ADR 0026 § 4: HOME is the one navigation input that is executed
    on the press that woke the panel.

    A person in the dark reaches for the way out once. Consumption exists to
    stop an unseen *context-dependent* action; HOME always lands on the same
    surface and stops nothing, so there is nothing to protect them from.

    Contrast `test_the_navigation_that_wakes_starts_nothing`: SELECT in the dark
    is consumed, because what it would start depends on invisible focus.
    """
    simulator, ui, session, display, _, _ = _core(tmp_path)
    simulator.handle_key("d")
    simulator.handle_key("s")
    assert ui.snapshot.surface is DeviceSurface.NOW_PLAYING
    display.set_night_active(True)
    assert display.snapshot.state is DisplayState.OFF

    assert simulator.handle_key("h")

    assert display.snapshot.state is DisplayState.INTERACTIVE
    assert ui.snapshot.surface is DeviceSurface.HOME
    assert session.snapshot.transport is TransportState.PLAYING
