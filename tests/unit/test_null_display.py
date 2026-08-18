from __future__ import annotations

from aqeno.adapters.display.none import NullDisplayPanel


def test_absent_panel_is_authoritatively_dark_and_accepts_output() -> None:
    panel = NullDisplayPanel()
    touches: list[bool] = []

    panel.set_power(True)
    panel.set_brightness(100)
    panel.on_touch(lambda: touches.append(True))

    assert panel.capabilities().authoritative_off is True
    assert panel.capabilities().brightness_control is False
    assert panel.capabilities().touch is False
    assert touches == []
