from __future__ import annotations

import pytest

from aqeno.adapters.input import KeyboardSimulator
from aqeno.ports.input import (
    InputEvent,
    Next,
    NfcPresented,
    NfcRemoved,
    Previous,
    TogglePlayback,
    VolumeDelta,
    WakeRequest,
)


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("up", VolumeDelta(1)),
        ("down", VolumeDelta(-1)),
        ("space", TogglePlayback()),
        ("right", Next()),
        ("left", Previous()),
        ("w", WakeRequest()),
        ("1", NfcPresented("AQENO-TEST-1")),
        ("9", NfcPresented("AQENO-TEST-9")),
    ],
)
def test_documented_key_emits_semantic_input(key: str, expected: InputEvent) -> None:
    simulator = KeyboardSimulator()
    received: list[InputEvent] = []
    simulator.on_input(received.append)

    assert simulator.handle_key(key)

    assert received == [expected]


def test_key_names_are_case_insensitive() -> None:
    simulator = KeyboardSimulator()
    received: list[InputEvent] = []
    simulator.on_input(received.append)

    assert simulator.handle_key("SPACE")

    assert received == [TogglePlayback()]


def test_zero_removes_the_presented_test_tag() -> None:
    simulator = KeyboardSimulator()
    received: list[InputEvent] = []
    simulator.on_input(received.append)

    simulator.handle_key("3")
    assert simulator.handle_key("0")

    assert received == [NfcPresented("AQENO-TEST-3"), NfcRemoved("AQENO-TEST-3")]


def test_zero_without_a_presented_tag_is_handled_without_emitting() -> None:
    simulator = KeyboardSimulator()
    received: list[InputEvent] = []
    simulator.on_input(received.append)

    assert simulator.handle_key("0")

    assert received == []


def test_night_key_controls_only_the_simulator_guard() -> None:
    toggles = 0

    def toggle_night() -> None:
        nonlocal toggles
        toggles += 1

    simulator = KeyboardSimulator(toggle_night=toggle_night)
    received: list[InputEvent] = []
    simulator.on_input(received.append)

    assert simulator.handle_key("n")

    assert toggles == 1
    assert received == []


def test_unknown_key_is_left_for_the_ui() -> None:
    simulator = KeyboardSimulator()

    assert not simulator.handle_key("escape")
