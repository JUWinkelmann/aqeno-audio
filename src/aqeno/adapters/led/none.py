"""Explicitly absent status LEDs for production compositions without RH1 LED I/O."""

from __future__ import annotations


class NullStatusLeds:
    """Keep the no-LED contract without pretending hardware exists."""

    def set_brightness(self, level: int) -> None:
        del level
