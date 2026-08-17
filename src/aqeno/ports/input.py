"""Semantic control input — ADR 0011 and `PLATFORM_CONTRACTS.md`.

GPIO pins, key codes and NFC reader details stop at an adapter. Application code receives only
these events.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, TypeAlias


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
class WakeRequest:
    pass


@dataclass(frozen=True, slots=True)
class NfcPresented:
    tag_id: str


@dataclass(frozen=True, slots=True)
class NfcRemoved:
    tag_id: str


InputEvent: TypeAlias = (
    VolumeDelta | TogglePlayback | Next | Previous | WakeRequest | NfcPresented | NfcRemoved
)
InputListener: TypeAlias = Callable[[InputEvent], None]


class InputBus(Protocol):
    """Delivers each input synchronously in listener registration order."""

    def on_input(self, listener: InputListener) -> None: ...
