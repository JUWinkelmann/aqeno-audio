"""Configuration — defaults and validation against `CONFIGURATION_DEFAULTS.md`.

Standard library only. No hardcoded timeout, brightness or volume value belongs
anywhere else (`DEVELOPMENT.md` § "Rules the layout enforces", rule 6).
"""

from aqeno.config.defaults import Settings, default_settings, validate
from aqeno.config.paths import config_dir, data_dir, database_path, settings_path, state_dir

__all__ = [
    "Settings",
    "config_dir",
    "data_dir",
    "database_path",
    "default_settings",
    "settings_path",
    "state_dir",
    "validate",
]
