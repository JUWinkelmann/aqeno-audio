"""Manager-tier configuration defaults and validation — `CONFIGURATION_DEFAULTS.md`.

Every value in that document, with its range, lives here and nowhere else
(`DEVELOPMENT.md` § "Rules the layout enforces", rule 6: no hardcoded timeout,
brightness or volume value at a call site).

`Settings` is the Manager tier from § 7: timeouts, brightness, volume ceilings,
sleep timer, NFC debounce and language. It is what `adapters/persistence/toml_settings.py`
reads from and writes to `settings.toml`. The settings file is untrusted input
(hand-editable, ADR 0007): `validate()` clamps out-of-range values to their range,
replaces unparseable ones with the default, and never raises — a malformed file
must never prevent startup.

"Fixed" values from `CONFIGURATION_DEFAULTS.md` (resume persist interval, fade
timings, the night LED value, the volume jump limit, ...) are not here: they are
not editable, so they are constants at their point of use, not settings.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, fields
from typing import Any


@dataclass(frozen=True, slots=True)
class IntRange:
    minimum: int
    maximum: int

    def contains(self, value: int) -> bool:
        return self.minimum <= value <= self.maximum

    def clamp(self, value: int) -> int:
        return max(self.minimum, min(self.maximum, value))


# ---------------------------------------------------------------------------
# § 1 Display timeouts
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DisplayTimeoutSettings:
    kids_early: int = 30
    kids_reader: int = 45
    kids_explorer: int = 60
    easy: int = 90
    standard: int = 120
    night_override: int = 10
    dim_hold_standard: int = 15
    setup_idle: int = 300
    setup_idle_night: int = 60


DISPLAY_TIMEOUT_RANGES: dict[str, IntRange] = {
    "kids_early": IntRange(10, 120),
    "kids_reader": IntRange(10, 180),
    "kids_explorer": IntRange(10, 300),
    "easy": IntRange(15, 600),
    "standard": IntRange(15, 900),
    "night_override": IntRange(5, 30),
    "dim_hold_standard": IntRange(5, 60),
    "setup_idle": IntRange(60, 900),
    "setup_idle_night": IntRange(30, 300),
}

# ---------------------------------------------------------------------------
# § 2 Brightness
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BrightnessSettings:
    interactive_kids_early: int = 70
    interactive_other_kids: int = 80
    interactive_easy: int = 85
    interactive_standard: int = 85
    dim_standard: int = 10
    """Only Standard ever reaches DIM; other profiles never read this."""
    ambient_kids_early: int = 40
    ambient_other_kids: int = 40
    ambient_easy: int = 50
    ambient_standard: int = 50
    night_minimum: int = 5
    led_normal: int = 20


_BRIGHTNESS_SCALE = IntRange(0, 100)
"""Logical 0-100 brightness scale (§ 2). The document gives no per-field range
beyond this scale for any brightness value, including the LED normal brightness."""

BRIGHTNESS_RANGES: dict[str, IntRange] = {
    f.name: _BRIGHTNESS_SCALE for f in fields(BrightnessSettings)
}

# ---------------------------------------------------------------------------
# § 3 Volume
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class VolumeSettings:
    child_maximum: int = 70
    night_ceiling: int = 35
    headphone_maximum: int = 55
    easy_standard_maximum: int = 100
    encoder_step: int = 3
    first_boot: int = 40


VOLUME_RANGES: dict[str, IntRange] = {
    "child_maximum": IntRange(30, 70),
    "night_ceiling": IntRange(15, 50),
    "headphone_maximum": IntRange(20, 60),
    "easy_standard_maximum": IntRange(50, 100),
    "encoder_step": IntRange(1, 10),
    # CONFIGURATION_DEFAULTS.md documents this as "0-ceiling", a range that
    # depends on the profile's own (also-configurable) ceiling and so cannot be
    # expressed as a single static range. 0-100 is the widest value that is ever
    # valid; the applicable per-profile ceiling clamp happens where volume is
    # loaded for a profile, not here.
    "first_boot": IntRange(0, 100),
}

# ---------------------------------------------------------------------------
# § 4 Resume — only the Manager-editable rewind is a setting
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ResumeSettings:
    rewind_seconds: int = 3


RESUME_RANGES: dict[str, IntRange] = {"rewind_seconds": IntRange(0, 10)}

# ---------------------------------------------------------------------------
# § 5 Scenes and sleep timer
# ---------------------------------------------------------------------------

_SLEEP_TIMER_PRESET_RANGE = IntRange(5, 120)
_SLEEP_TIMER_ACTIONS = ("pause", "stop")


@dataclass(frozen=True, slots=True)
class SleepTimerSettings:
    duration_minutes: int = 30
    presets_minutes: tuple[int, ...] = (15, 30, 45, 60)
    fade_out_seconds: int = 20
    action_at_end: str = "pause"


SLEEP_TIMER_RANGES: dict[str, IntRange] = {
    "duration_minutes": IntRange(5, 120),
    "fade_out_seconds": IntRange(0, 60),
}

# ---------------------------------------------------------------------------
# § 6 NFC
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class NfcSettings:
    debounce_ms: int = 2000
    ack_tone_unassigned: bool = False


NFC_RANGES: dict[str, IntRange] = {"debounce_ms": IntRange(500, 5000)}

# ---------------------------------------------------------------------------
# Language — ADR 0005
# ---------------------------------------------------------------------------

SUPPORTED_LANGUAGES = ("de", "en")


def default_language() -> str:
    """System locale when it is German or English, else English.

    ADR 0005: "Initial value is offered during SETUP, defaulting to the system
    locale when it is German or English."
    """
    raw = os.environ.get("LANG", "")
    code = raw.split("_")[0].split(".")[0].lower()
    return code if code in SUPPORTED_LANGUAGES else "en"


# ---------------------------------------------------------------------------
# The settings bundle
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Settings:
    display: DisplayTimeoutSettings = field(default_factory=DisplayTimeoutSettings)
    brightness: BrightnessSettings = field(default_factory=BrightnessSettings)
    volume: VolumeSettings = field(default_factory=VolumeSettings)
    resume: ResumeSettings = field(default_factory=ResumeSettings)
    sleep_timer: SleepTimerSettings = field(default_factory=SleepTimerSettings)
    nfc: NfcSettings = field(default_factory=NfcSettings)
    language: str = field(default_factory=default_language)


def default_settings() -> Settings:
    return Settings()


_SECTIONS: tuple[tuple[str, type, dict[str, IntRange]], ...] = (
    ("display", DisplayTimeoutSettings, DISPLAY_TIMEOUT_RANGES),
    ("brightness", BrightnessSettings, BRIGHTNESS_RANGES),
    ("volume", VolumeSettings, VOLUME_RANGES),
    ("resume", ResumeSettings, RESUME_RANGES),
    ("nfc", NfcSettings, NFC_RANGES),
)


def _validate_int_section(
    section_name: str,
    section_type: type,
    ranges: dict[str, IntRange],
    raw: Any,
    warnings: list[str],
) -> Any:
    defaults = section_type()
    raw_section = raw if isinstance(raw, dict) else {}
    if raw is not None and not isinstance(raw, dict):
        warnings.append(
            f"{section_name}: expected a table, got {type(raw).__name__}; using defaults"
        )
    kwargs: dict[str, Any] = {}
    for f in fields(section_type):
        default_value = getattr(defaults, f.name)
        value = raw_section.get(f.name, default_value)
        key = f"{section_name}.{f.name}"
        if f.type is bool or isinstance(default_value, bool):
            if not isinstance(value, bool):
                warnings.append(f"{key}: expected true/false, got {value!r}; using default")
                value = default_value
            kwargs[f.name] = value
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            warnings.append(
                f"{key}: expected an integer, got {value!r}; using default {default_value}"
            )
            value = default_value
        rng = ranges.get(f.name)
        if rng is not None and not rng.contains(value):
            clamped = rng.clamp(value)
            warnings.append(
                f"{key}: {value} is outside {rng.minimum}-{rng.maximum}; clamped to {clamped}"
            )
            value = clamped
        kwargs[f.name] = value
    return section_type(**kwargs)


def _validate_sleep_timer(raw: Any, warnings: list[str]) -> SleepTimerSettings:
    defaults = SleepTimerSettings()
    raw_section = raw if isinstance(raw, dict) else {}
    if raw is not None and not isinstance(raw, dict):
        warnings.append(f"sleep_timer: expected a table, got {type(raw).__name__}; using defaults")

    duration = raw_section.get("duration_minutes", defaults.duration_minutes)
    if isinstance(duration, bool) or not isinstance(duration, int):
        warnings.append(f"sleep_timer.duration_minutes: invalid value {duration!r}; using default")
        duration = defaults.duration_minutes
    rng = SLEEP_TIMER_RANGES["duration_minutes"]
    if not rng.contains(duration):
        clamped = rng.clamp(duration)
        warnings.append(
            f"sleep_timer.duration_minutes: {duration} out of range; clamped to {clamped}"
        )
        duration = clamped

    fade_out = raw_section.get("fade_out_seconds", defaults.fade_out_seconds)
    if isinstance(fade_out, bool) or not isinstance(fade_out, int):
        warnings.append(f"sleep_timer.fade_out_seconds: invalid value {fade_out!r}; using default")
        fade_out = defaults.fade_out_seconds
    rng = SLEEP_TIMER_RANGES["fade_out_seconds"]
    if not rng.contains(fade_out):
        clamped = rng.clamp(fade_out)
        warnings.append(
            f"sleep_timer.fade_out_seconds: {fade_out} out of range; clamped to {clamped}"
        )
        fade_out = clamped

    presets_raw = raw_section.get("presets_minutes", defaults.presets_minutes)
    presets: list[int] = []
    if isinstance(presets_raw, list | tuple) and all(
        isinstance(p, int) and not isinstance(p, bool) for p in presets_raw
    ):
        for p in presets_raw:
            if _SLEEP_TIMER_PRESET_RANGE.contains(p):
                presets.append(p)
            else:
                clamped = _SLEEP_TIMER_PRESET_RANGE.clamp(p)
                warnings.append(
                    f"sleep_timer.presets_minutes: {p} out of range; clamped to {clamped}"
                )
                presets.append(clamped)
    else:
        warnings.append("sleep_timer.presets_minutes: invalid value; using defaults")
        presets = list(defaults.presets_minutes)

    action = raw_section.get("action_at_end", defaults.action_at_end)
    if action not in _SLEEP_TIMER_ACTIONS:
        warnings.append(
            f"sleep_timer.action_at_end: {action!r} is not one of "
            f"{_SLEEP_TIMER_ACTIONS}; using default"
        )
        action = defaults.action_at_end

    return SleepTimerSettings(
        duration_minutes=duration,
        presets_minutes=tuple(presets),
        fade_out_seconds=fade_out,
        action_at_end=action,
    )


def validate(raw: dict[str, Any] | None) -> tuple[Settings, list[str]]:
    """Validate a raw parsed-TOML mapping against every range in this module.

    Returns the resulting `Settings` plus a list of human-readable warnings for
    anything clamped or defaulted. Never raises: an unparseable or missing value
    at any key falls back to its default. The caller (the TOML adapter) logs the
    warnings and leaves the file on disk untouched — this function never writes.
    """
    raw = raw if isinstance(raw, dict) else {}
    warnings: list[str] = []

    kwargs: dict[str, Any] = {}
    for section_name, section_type, ranges in _SECTIONS:
        kwargs[section_name] = _validate_int_section(
            section_name, section_type, ranges, raw.get(section_name), warnings
        )
    kwargs["sleep_timer"] = _validate_sleep_timer(raw.get("sleep_timer"), warnings)

    language = raw.get("language", default_language())
    if language not in SUPPORTED_LANGUAGES:
        warnings.append(
            f"language: {language!r} is not one of {SUPPORTED_LANGUAGES}; using default"
        )
        language = default_language()
    kwargs["language"] = language

    return Settings(**kwargs), warnings
