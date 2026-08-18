"""RH1 I2C controls adapter.

The concrete Adafruit imports are confined to :func:`open_reference_input`.
The polling adapter itself only depends on the small device protocols below,
which keeps its event and edge behaviour deterministic without a Raspberry Pi.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable, Sequence
from typing import Protocol

from aqeno.ports.input import (
    InputEvent,
    InputListener,
    Next,
    Previous,
    TogglePlayback,
    VolumeDelta,
)

logger = logging.getLogger(__name__)


class _Encoder(Protocol):
    def position(self) -> int: ...

    def pressed(self) -> bool: ...


class _Keys(Protocol):
    def pressed_keys(self) -> Sequence[bool]: ...


class I2cSeesawInputBus:
    """Poll RH1's rotary encoder and NeoKey board into semantic events.

    ``start`` is deliberately separate from construction.  The composition
    root registers all application listeners before starting the daemon poller,
    as required by ADR 0011 and the readiness contract.
    """

    def __init__(
        self,
        *,
        encoder: _Encoder,
        keys: _Keys,
        poll_interval: float = 0.02,
        wait: Callable[[float], bool | None] | None = None,
    ) -> None:
        if poll_interval <= 0:
            raise ValueError("poll_interval must be positive")
        self._encoder = encoder
        self._keys = keys
        self._poll_interval = poll_interval
        self._stop = threading.Event()
        self._wait = wait or self._stop.wait
        self._listeners: list[InputListener] = []
        self._listeners_lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._started = False
        self._last_position: int | None = None
        self._button_pressed = False
        self._keys_pressed: tuple[bool, ...] = ()

    def on_input(self, listener: InputListener) -> None:
        with self._listeners_lock:
            self._listeners.append(listener)

    def start(self) -> None:
        """Start polling exactly once; no hardware is read before this call."""
        if self._started:
            return
        self._started = True
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="aqeno-rh1-input",
            daemon=True,
        )
        self._thread.start()

    def close(self) -> None:
        """Stop the poller and wait for an in-flight poll to finish."""
        self._stop.set()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join()
        self._thread = None
        self._started = False

    def poll_once(self) -> None:
        """Poll once; public for deterministic adapter and hardware tests."""
        position = self._encoder.position()
        button_pressed = self._encoder.pressed()
        keys_pressed = tuple(bool(value) for value in self._keys.pressed_keys())

        if self._last_position is None:
            self._last_position = position
            self._button_pressed = button_pressed
            self._keys_pressed = keys_pressed
            return

        delta = self._last_position - position
        self._last_position = position
        if delta:
            # The seesaw encoder increases in the opposite direction from the
            # product's clockwise-positive convention.
            self._emit(VolumeDelta(delta))

        if button_pressed and not self._button_pressed:
            self._emit(TogglePlayback())
        self._button_pressed = button_pressed

        for index, pressed in enumerate(keys_pressed):
            if not pressed or index >= len(self._keys_pressed) or self._keys_pressed[index]:
                continue
            if index == 0:
                self._emit(Previous())
            elif index == 2:
                self._emit(Next())
        self._keys_pressed = keys_pressed

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self.poll_once()
            except Exception:
                # A transient I2C read failure must not take down playback or
                # make the daemon thread silently disappear.
                logger.exception("RH1 input poll failed")
            if self._wait(self._poll_interval):
                break

    def _emit(self, event: InputEvent) -> None:
        with self._listeners_lock:
            listeners = tuple(self._listeners)
        for listener in listeners:
            # ADR 0011 deliberately gives every InputBus the same fail-fast
            # synchronous delivery contract. The polling loop contains the
            # failure at the hardware-thread boundary and retries later.
            listener(event)


class _SeesawEncoder:
    def __init__(self, encoder: object, button: object) -> None:
        self._encoder = encoder
        self._button = button

    def position(self) -> int:
        return int(self._encoder.position)  # type: ignore[attr-defined]

    def pressed(self) -> bool:
        return not bool(self._button.value)  # type: ignore[attr-defined]


class _NeoKey:
    def __init__(self, device: object) -> None:
        self._device = device

    def pressed_keys(self) -> Sequence[bool]:
        values = self._device.get_keys()  # type: ignore[attr-defined]
        return tuple(bool(value) for value in values)


def open_reference_input() -> I2cSeesawInputBus:
    """Construct the RH1 control adapter, importing hardware drivers lazily."""
    import board
    from adafruit_neokey.neokey1x4 import NeoKey1x4
    from adafruit_seesaw import digitalio, rotaryio, seesaw

    i2c = board.I2C()
    encoder_seesaw = seesaw.Seesaw(i2c, addr=0x36)
    encoder = rotaryio.IncrementalEncoder(encoder_seesaw)
    encoder_seesaw.pin_mode(24, encoder_seesaw.INPUT_PULLUP)
    button = digitalio.DigitalIO(encoder_seesaw, 24)
    keys = NeoKey1x4(i2c, addr=0x30)
    return I2cSeesawInputBus(
        encoder=_SeesawEncoder(encoder, button),
        keys=_NeoKey(keys),
    )
