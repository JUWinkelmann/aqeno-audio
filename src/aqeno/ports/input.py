"""Semantic control input — ADR 0011 and `PLATFORM_CONTRACTS.md`.

GPIO pins, key codes and NFC reader details stop at an adapter. Application code receives only
these events.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, TypeAlias


class LogicalControl(StrEnum):
    """Stable product-facing controls; never board channels or bus addresses."""

    PRIMARY_LEFT = "primary_left"
    PRIMARY_ENCODER = "primary_encoder"
    PRIMARY_RIGHT = "primary_right"
    NAVIGATION_ENCODER = "navigation_encoder"


class ControlEventType(StrEnum):
    SHORT_PRESS = "short_press"
    LONG_PRESS = "long_press"
    ROTATE_LEFT = "rotate_left"
    ROTATE_RIGHT = "rotate_right"


class ControlType(StrEnum):
    BUTTON = "button"
    ROTARY_ENCODER = "rotary_encoder"


@dataclass(frozen=True, slots=True)
class ControlInput:
    """One normalized physical event before AQENO action mapping."""

    control: LogicalControl
    event: ControlEventType


@dataclass(frozen=True, slots=True)
class ControlCapability:
    control: LogicalControl
    type: ControlType
    label: str
    events: tuple[ControlEventType, ...]
    illumination: bool


ControlInputListener: TypeAlias = Callable[[ControlInput], None]


class PhysicalInputSource(Protocol):
    """Hardware boundary below configurable AQENO action mapping."""

    @property
    def controls(self) -> tuple[ControlCapability, ...]: ...

    def on_control_input(self, listener: ControlInputListener) -> None: ...


@dataclass(frozen=True, slots=True)
class VolumeDelta:
    delta: int


@dataclass(frozen=True, slots=True)
class TogglePlayback:
    pass


@dataclass(frozen=True, slots=True)
class Next:
    pass


@dataclass(frozen=True, slots=True)
class Previous:
    pass


@dataclass(frozen=True, slots=True)
class Play:
    pass


@dataclass(frozen=True, slots=True)
class Pause:
    pass


@dataclass(frozen=True, slots=True)
class Stop:
    pass


@dataclass(frozen=True, slots=True)
class WakeRequest:
    pass


# Navigation (ADR 0024). Deliberately named apart from the transport `Previous`
# and `Next` above: a person operating AQENO without looking must be able to
# rely on transport and navigation never trading places, and a reader of this
# file should not have to work out which `Next` is meant.


@dataclass(frozen=True, slots=True)
class FocusPrevious:
    pass


@dataclass(frozen=True, slots=True)
class FocusNext:
    pass


@dataclass(frozen=True, slots=True)
class Select:
    pass


@dataclass(frozen=True, slots=True)
class Back:
    pass


@dataclass(frozen=True, slots=True)
class NfcPresented:
    tag_id: str


@dataclass(frozen=True, slots=True)
class NfcRemoved:
    tag_id: str


InputEvent: TypeAlias = (
    VolumeDelta
    | TogglePlayback
    | Next
    | Previous
    | Play
    | Pause
    | Stop
    | WakeRequest
    | FocusPrevious
    | FocusNext
    | Select
    | Back
    | NfcPresented
    | NfcRemoved
)

NAVIGATION_EVENTS: tuple[type, ...] = (FocusPrevious, FocusNext, Select, Back)
"""Group G in `DISPLAY_STATE_MACHINE.md`: these wake the display like a touch,
and the one that wakes it is consumed. Transport never does either."""
InputListener: TypeAlias = Callable[[InputEvent], None]


class InputBus(Protocol):
    """Delivers each input synchronously in listener registration order."""

    def on_input(self, listener: InputListener) -> None: ...
