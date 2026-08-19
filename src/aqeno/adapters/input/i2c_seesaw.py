"""RH1 I2C controls adapter.

The concrete Adafruit imports are confined to :func:`open_reference_input`.
The polling adapter itself only depends on the small device protocols below,
which keeps its event and edge behaviour deterministic without a Raspberry Pi.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable, Sequence
from typing import Protocol

from aqeno.ports.input import (
    ControlCapability,
    ControlEventType,
    ControlInput,
    ControlInputListener,
    ControlType,
    LogicalControl,
)

logger = logging.getLogger(__name__)

LONG_PRESS_SECONDS = 0.8
"""One product threshold for every RH1 push control."""

RH1_KEY_CONTROLS = {
    0: LogicalControl.PREVIOUS,
    1: LogicalControl.NEXT,
    3: LogicalControl.HOME,
}
"""NeoKey socket → AQENO control (ADR 0026 § 2).

PREVIOUS and NEXT sit adjacent so the transport pair reads as one pair by hand;
socket 2 is left empty so HOME is physically separated from them (Tactile
Identity). Socket positions are fixed by the board, so this mapping is where
that layout decision lives — and it stays provisional until the assembled unit
is felt in the dark (`RH1_VALIDATION_CHECKLIST.md`).

RH1 has no SELECT encoder. Its bindings exist and report as unavailable, which
is the same honest state as any other absent hardware."""

RH1_CONTROL_CAPABILITIES = (
    ControlCapability(
        LogicalControl.PREVIOUS,
        ControlType.BUTTON,
        "Zurück im Inhalt",
        (ControlEventType.SHORT_PRESS, ControlEventType.LONG_PRESS),
        True,
    ),
    ControlCapability(
        LogicalControl.NEXT,
        ControlType.BUTTON,
        "Weiter im Inhalt",
        (ControlEventType.SHORT_PRESS, ControlEventType.LONG_PRESS),
        True,
    ),
    ControlCapability(
        LogicalControl.VOLUME_ENCODER,
        ControlType.ROTARY_ENCODER,
        "Lautstärke",
        (
            ControlEventType.ROTATE_LEFT,
            ControlEventType.ROTATE_RIGHT,
            ControlEventType.SHORT_PRESS,
            ControlEventType.LONG_PRESS,
        ),
        True,
    ),
    ControlCapability(
        LogicalControl.HOME,
        ControlType.BUTTON,
        "Startseite",
        (ControlEventType.SHORT_PRESS, ControlEventType.LONG_PRESS),
        True,
    ),
)


class PressGestureRecognizer:
    """Derive exactly one short or long gesture from button edges and duration."""

    def __init__(self, *, threshold: float = LONG_PRESS_SECONDS) -> None:
        if threshold <= 0:
            raise ValueError("long press threshold must be positive")
        self._threshold = threshold
        self._started_at: float | None = None
        self._long_emitted = False

    def prime(self, pressed: bool, now: float) -> None:
        self._started_at = now if pressed else None
        self._long_emitted = pressed

    def update(self, pressed: bool, now: float) -> ControlEventType | None:
        if pressed:
            if self._started_at is None:
                self._started_at = now
                self._long_emitted = False
            if not self._long_emitted and now - self._started_at >= self._threshold:
                self._long_emitted = True
                return ControlEventType.LONG_PRESS
            return None

        if self._started_at is None:
            return None
        was_long = self._long_emitted
        self._started_at = None
        self._long_emitted = False
        return None if was_long else ControlEventType.SHORT_PRESS


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
        monotonic: Callable[[], float] = time.monotonic,
        long_press_seconds: float = LONG_PRESS_SECONDS,
    ) -> None:
        if poll_interval <= 0:
            raise ValueError("poll_interval must be positive")
        self._encoder = encoder
        self._keys = keys
        self._poll_interval = poll_interval
        self._stop = threading.Event()
        self._wait = wait or self._stop.wait
        self._listeners: list[ControlInputListener] = []
        self._listeners_lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._started = False
        self._last_position: int | None = None
        self._keys_pressed: tuple[bool, ...] = ()
        self._monotonic = monotonic
        self._encoder_press = PressGestureRecognizer(threshold=long_press_seconds)
        self._key_presses = {
            index: PressGestureRecognizer(threshold=long_press_seconds)
            for index in RH1_KEY_CONTROLS
        }

    @property
    def controls(self) -> tuple[ControlCapability, ...]:
        return RH1_CONTROL_CAPABILITIES

    def on_control_input(self, listener: ControlInputListener) -> None:
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
        now = self._monotonic()

        if self._last_position is None:
            self._last_position = position
            self._keys_pressed = keys_pressed
            self._encoder_press.prime(button_pressed, now)
            for index, recognizer in self._key_presses.items():
                recognizer.prime(index < len(keys_pressed) and keys_pressed[index], now)
            return

        delta = self._last_position - position
        self._last_position = position
        if delta:
            # Adafruit's official example normalizes this board as
            # ``position = -encoder.position``. Keep that hardware detail here.
            rotation_event = (
                ControlEventType.ROTATE_RIGHT if delta > 0 else ControlEventType.ROTATE_LEFT
            )
            for _ in range(abs(delta)):
                self._emit(ControlInput(LogicalControl.VOLUME_ENCODER, rotation_event))

        encoder_event = self._encoder_press.update(button_pressed, now)
        if encoder_event is not None:
            self._emit(ControlInput(LogicalControl.VOLUME_ENCODER, encoder_event))

        for index, recognizer in self._key_presses.items():
            pressed = index < len(keys_pressed) and keys_pressed[index]
            key_event = recognizer.update(pressed, now)
            if key_event is not None:
                self._emit(ControlInput(RH1_KEY_CONTROLS[index], key_event))
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

    def _emit(self, event: ControlInput) -> None:
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
    import board  # type: ignore[import-not-found]
    from adafruit_neokey.neokey1x4 import NeoKey1x4  # type: ignore[import-not-found]
    from adafruit_seesaw import digitalio, rotaryio, seesaw  # type: ignore[import-not-found]

    i2c = board.I2C()
    encoder_seesaw = seesaw.Seesaw(i2c, addr=0x36)
    encoder = rotaryio.IncrementalEncoder(encoder_seesaw)
    # Adafruit PID 5880: push button is seesaw pin 24. The board's NeoPixel is
    # pin 6 and is owned by the separate RH1 LED adapter.
    encoder_seesaw.pin_mode(24, encoder_seesaw.INPUT_PULLUP)
    button = digitalio.DigitalIO(encoder_seesaw, 24)
    keys = NeoKey1x4(i2c, addr=0x30)
    return I2cSeesawInputBus(
        encoder=_SeesawEncoder(encoder, button),
        keys=_NeoKey(keys),
    )
