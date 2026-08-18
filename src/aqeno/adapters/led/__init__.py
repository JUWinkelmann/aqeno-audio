"""Status LED adapters."""

from aqeno.adapters.led.i2c_seesaw import Rh1StatusLeds, open_reference_leds
from aqeno.adapters.led.none import NullStatusLeds

__all__ = ["NullStatusLeds", "Rh1StatusLeds", "open_reference_leds"]
