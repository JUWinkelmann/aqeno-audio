"""RH1 user-facing illumination adapter.

Product policy supplies only brightness.  The restrained AQENO warm-white
output and the Adafruit pin/channel details remain inside this adapter.
"""

from __future__ import annotations

from typing import Protocol


class _Pixels(Protocol):
    brightness: float

    def fill(self, color: tuple[int, int, int]) -> None: ...


_AQENO_WARM = (255, 214, 184)


class Rh1StatusLeds:
    def __init__(self, *, encoder_pixel: _Pixels, key_pixels: _Pixels) -> None:
        self._encoder_pixel = encoder_pixel
        self._key_pixels = key_pixels

    def set_brightness(self, level: int) -> None:
        normalized = max(0, min(level, 100)) / 100
        color = _AQENO_WARM if level > 0 else (0, 0, 0)
        for pixels in (self._encoder_pixel, self._key_pixels):
            pixels.brightness = normalized
            pixels.fill(color)


def open_reference_leds() -> Rh1StatusLeds:
    """Open PID 5880 pin 6 and NeoKey 1x4 pixels using official libraries."""
    import board  # type: ignore[import-not-found]
    from adafruit_neokey.neokey1x4 import NeoKey1x4  # type: ignore[import-not-found]
    from adafruit_seesaw import neopixel, seesaw  # type: ignore[import-not-found]

    i2c = board.I2C()
    encoder_seesaw = seesaw.Seesaw(i2c, addr=0x36)
    encoder_pixel = neopixel.NeoPixel(encoder_seesaw, 6, 1)
    key_pixels = NeoKey1x4(i2c, addr=0x30).pixels
    return Rh1StatusLeds(encoder_pixel=encoder_pixel, key_pixels=key_pixels)
