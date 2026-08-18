from __future__ import annotations

from dataclasses import dataclass, field

from aqeno.adapters.led.i2c_seesaw import Rh1StatusLeds


@dataclass
class Pixels:
    brightness: float = 0.0
    colors: list[tuple[int, int, int]] = field(default_factory=list)

    def fill(self, color: tuple[int, int, int]) -> None:
        self.colors.append(color)


def test_rh1_led_adapter_exposes_brightness_not_raw_user_rgb() -> None:
    encoder = Pixels()
    keys = Pixels()
    leds = Rh1StatusLeds(encoder_pixel=encoder, key_pixels=keys)

    leds.set_brightness(20)

    assert encoder.brightness == keys.brightness == 0.2
    assert encoder.colors == keys.colors
    assert encoder.colors[-1] != (0, 0, 0)


def test_zero_is_true_off_and_brightness_is_bounded() -> None:
    encoder = Pixels()
    keys = Pixels()
    leds = Rh1StatusLeds(encoder_pixel=encoder, key_pixels=keys)

    leds.set_brightness(400)
    assert encoder.brightness == keys.brightness == 1.0

    leds.set_brightness(0)
    assert encoder.brightness == keys.brightness == 0.0
    assert encoder.colors[-1] == keys.colors[-1] == (0, 0, 0)
