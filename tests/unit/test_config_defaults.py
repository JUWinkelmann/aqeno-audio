"""Settings validation against `CONFIGURATION_DEFAULTS.md` — ADR 0007 § "Settings".

The settings file is untrusted input: a malformed or out-of-range value must
never prevent startup, must be clamped or defaulted, and the file itself is
left untouched (`validate()` never writes anything).
"""

from __future__ import annotations

from aqeno.config.defaults import (
    BRIGHTNESS_RANGES,
    DISPLAY_TIMEOUT_RANGES,
    NFC_RANGES,
    RESUME_RANGES,
    SLEEP_TIMER_RANGES,
    SUPPORTED_LANGUAGES,
    VOLUME_RANGES,
    Settings,
    default_settings,
    validate,
)


class TestDefaultsMatchTheDocument:
    """Every default in `CONFIGURATION_DEFAULTS.md`, transcribed once."""

    def test_display_timeouts(self) -> None:
        d = default_settings().display
        assert (d.kids_early, d.kids_reader, d.kids_explorer, d.easy, d.standard) == (
            30,
            45,
            60,
            90,
            120,
        )
        assert (d.night_override, d.dim_hold_standard, d.setup_idle, d.setup_idle_night) == (
            10,
            15,
            300,
            60,
        )

    def test_brightness(self) -> None:
        b = default_settings().brightness
        assert b.interactive_kids_early == 70
        assert b.interactive_other_kids == 80
        assert b.interactive_easy == 85
        assert b.interactive_standard == 85
        assert b.dim_standard == 10
        assert b.ambient_kids_early == 40
        assert b.ambient_standard == 50
        assert b.night_minimum == 5
        assert b.led_normal == 20

    def test_volume(self) -> None:
        v = default_settings().volume
        assert v.child_maximum == 70
        assert v.night_ceiling == 35
        assert v.headphone_maximum == 55
        assert v.easy_standard_maximum == 100
        assert v.encoder_step == 3
        assert v.first_boot == 40

    def test_resume(self) -> None:
        assert default_settings().resume.rewind_seconds == 3

    def test_sleep_timer(self) -> None:
        s = default_settings().sleep_timer
        assert s.duration_minutes == 30
        assert s.presets_minutes == (15, 30, 45, 60)
        assert s.fade_out_seconds == 20
        assert s.action_at_end == "pause"

    def test_nfc(self) -> None:
        n = default_settings().nfc
        assert n.debounce_ms == 2000
        assert n.ack_tone_unassigned is False


class TestRangesMatchTheDocument:
    def test_display_timeout_ranges(self) -> None:
        assert DISPLAY_TIMEOUT_RANGES["kids_early"].minimum == 10
        assert DISPLAY_TIMEOUT_RANGES["kids_early"].maximum == 120
        assert DISPLAY_TIMEOUT_RANGES["kids_reader"].maximum == 180
        assert DISPLAY_TIMEOUT_RANGES["kids_explorer"].maximum == 300
        assert DISPLAY_TIMEOUT_RANGES["easy"].minimum == 15
        assert DISPLAY_TIMEOUT_RANGES["easy"].maximum == 600
        assert DISPLAY_TIMEOUT_RANGES["standard"].maximum == 900
        assert DISPLAY_TIMEOUT_RANGES["night_override"].minimum == 5
        assert DISPLAY_TIMEOUT_RANGES["night_override"].maximum == 30
        assert DISPLAY_TIMEOUT_RANGES["dim_hold_standard"].maximum == 60
        assert DISPLAY_TIMEOUT_RANGES["setup_idle"].minimum == 60
        assert DISPLAY_TIMEOUT_RANGES["setup_idle"].maximum == 900
        assert DISPLAY_TIMEOUT_RANGES["setup_idle_night"].minimum == 30
        assert DISPLAY_TIMEOUT_RANGES["setup_idle_night"].maximum == 300

    def test_brightness_range_is_the_logical_scale(self) -> None:
        for rng in BRIGHTNESS_RANGES.values():
            assert (rng.minimum, rng.maximum) == (0, 100)

    def test_volume_ranges(self) -> None:
        assert (VOLUME_RANGES["child_maximum"].minimum, VOLUME_RANGES["child_maximum"].maximum) == (
            30,
            70,
        )
        assert (VOLUME_RANGES["night_ceiling"].minimum, VOLUME_RANGES["night_ceiling"].maximum) == (
            15,
            50,
        )
        assert (
            VOLUME_RANGES["headphone_maximum"].minimum,
            VOLUME_RANGES["headphone_maximum"].maximum,
        ) == (20, 60)
        assert (
            VOLUME_RANGES["easy_standard_maximum"].minimum,
            VOLUME_RANGES["easy_standard_maximum"].maximum,
        ) == (50, 100)
        assert (VOLUME_RANGES["encoder_step"].minimum, VOLUME_RANGES["encoder_step"].maximum) == (
            1,
            10,
        )

    def test_resume_range(self) -> None:
        rewind = RESUME_RANGES["rewind_seconds"]
        assert (rewind.minimum, rewind.maximum) == (0, 10)

    def test_sleep_timer_ranges(self) -> None:
        assert (
            SLEEP_TIMER_RANGES["duration_minutes"].minimum,
            SLEEP_TIMER_RANGES["duration_minutes"].maximum,
        ) == (5, 120)
        assert (
            SLEEP_TIMER_RANGES["fade_out_seconds"].minimum,
            SLEEP_TIMER_RANGES["fade_out_seconds"].maximum,
        ) == (0, 60)

    def test_nfc_range(self) -> None:
        assert (NFC_RANGES["debounce_ms"].minimum, NFC_RANGES["debounce_ms"].maximum) == (500, 5000)

    def test_child_maximum_can_never_be_configured_above_the_hard_ceiling(self) -> None:
        """VolumeLimits.CHILD_HARD_MAXIMUM in domain/profile.py must agree with this."""
        from aqeno.domain.profile import VolumeLimits

        assert VOLUME_RANGES["child_maximum"].maximum == VolumeLimits.CHILD_HARD_MAXIMUM


class TestValidateNeverRaises:
    def test_none_input_yields_defaults(self) -> None:
        settings, warnings = validate(None)
        assert settings == default_settings()
        assert warnings == []

    def test_empty_dict_yields_defaults(self) -> None:
        settings, warnings = validate({})
        assert settings == default_settings()
        assert warnings == []

    def test_garbage_top_level_types_do_not_raise(self) -> None:
        settings, warnings = validate({"display": "not a table", "volume": 42, "language": 7})
        assert isinstance(settings, Settings)
        assert len(warnings) >= 3

    def test_wrong_type_scalar_falls_back_to_default(self) -> None:
        settings, warnings = validate({"volume": {"child_maximum": "loud"}})
        assert settings.volume.child_maximum == default_settings().volume.child_maximum
        assert any("child_maximum" in w for w in warnings)


class TestClamping:
    def test_out_of_range_is_clamped_not_rejected(self) -> None:
        settings, warnings = validate({"volume": {"child_maximum": 999}})
        assert settings.volume.child_maximum == 70
        assert any("child_maximum" in w for w in warnings)

    def test_below_minimum_is_clamped(self) -> None:
        settings, _warnings = validate({"display": {"kids_early": 1}})
        assert settings.display.kids_early == 10

    def test_child_maximum_cannot_be_raised_above_seventy_via_settings_file(self) -> None:
        """The settings file is untrusted; the hard ceiling still applies."""
        settings, _ = validate({"volume": {"child_maximum": 100}})
        assert settings.volume.child_maximum <= 70

    def test_bool_is_not_accepted_as_an_int(self) -> None:
        """bool is a subclass of int in Python; a stray `true` must not become 1."""
        settings, warnings = validate({"volume": {"encoder_step": True}})
        assert settings.volume.encoder_step == default_settings().volume.encoder_step
        assert any("encoder_step" in w for w in warnings)


class TestSleepTimerPresets:
    def test_out_of_range_presets_are_clamped_individually(self) -> None:
        settings, warnings = validate({"sleep_timer": {"presets_minutes": [1, 30, 500]}})
        assert settings.sleep_timer.presets_minutes == (5, 30, 120)
        assert len(warnings) == 2

    def test_invalid_action_falls_back_to_pause(self) -> None:
        settings, warnings = validate({"sleep_timer": {"action_at_end": "explode"}})
        assert settings.sleep_timer.action_at_end == "pause"
        assert warnings


class TestLanguage:
    def test_unsupported_language_falls_back(self) -> None:
        settings, warnings = validate({"language": "fr"})
        assert settings.language in SUPPORTED_LANGUAGES
        assert warnings

    def test_supported_language_is_kept(self) -> None:
        settings, warnings = validate({"language": "en"})
        assert settings.language == "en"
        assert warnings == []
