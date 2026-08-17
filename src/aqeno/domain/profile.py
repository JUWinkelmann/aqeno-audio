"""Roles, experience profiles and the capability model.

Roles are User / Manager / Owner, never Parent / Child (`AGENTS.md`). Kids and Easy
are one adaptive core driven by capabilities, not two applications.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum, auto


class Role(StrEnum):
    USER = auto()
    MANAGER = auto()
    OWNER = auto()

    def may_manage(self) -> bool:
        return self in (Role.MANAGER, Role.OWNER)


class ExperienceLevel(StrEnum):
    KIDS_EARLY = auto()
    KIDS_READER = auto()
    KIDS_EXPLORER = auto()
    EASY = auto()
    STANDARD = auto()

    @property
    def is_child(self) -> bool:
        return self in (
            ExperienceLevel.KIDS_EARLY,
            ExperienceLevel.KIDS_READER,
            ExperienceLevel.KIDS_EXPLORER,
        )


@dataclass(frozen=True, slots=True)
class DisplayPolicy:
    """Values come from CONFIGURATION_DEFAULTS.md; never hardcode them at a call site."""

    inactivity_timeout: timedelta
    night_timeout: timedelta
    allows_dim: bool
    dim_hold: timedelta | None
    interactive_brightness: int
    dim_brightness: int
    ambient_brightness: int
    night_brightness: int
    led_brightness: int


@dataclass(frozen=True, slots=True)
class VolumeLimits:
    """Safety-critical (ADR 0006 § 6). These are hearing protection, not preferences.

    The logical scale is not a dB guarantee — see CONFIGURATION_DEFAULTS.md § 3.3 and
    the calibration procedure that replaces these placeholders with measured values.
    """

    maximum: int
    night_maximum: int
    headphone_maximum: int

    CHILD_HARD_MAXIMUM = 70
    """A Manager may lower a child ceiling, never raise it above this."""

    def ceiling(self, *, night_active: bool, headphones: bool) -> int:
        limits = [self.maximum]
        if night_active:
            limits.append(self.night_maximum)
        if headphones:
            limits.append(self.headphone_maximum)
        return min(limits)

    def clamp(self, volume: int, *, night_active: bool, headphones: bool) -> int:
        ceiling = self.ceiling(night_active=night_active, headphones=headphones)
        return max(0, min(volume, ceiling))


@dataclass(frozen=True, slots=True)
class Profile:
    name: str
    level: ExperienceLevel
    role: Role
    display: DisplayPolicy
    volume: VolumeLimits
    ambient_enabled: bool = False
    """Disabled by default for child profiles; Manager/Owner controlled."""

    def __post_init__(self) -> None:
        if self.level.is_child and self.volume.maximum > VolumeLimits.CHILD_HARD_MAXIMUM:
            raise ValueError(
                f"child profile {self.name!r} exceeds the hard volume ceiling "
                f"({self.volume.maximum} > {VolumeLimits.CHILD_HARD_MAXIMUM})"
            )
