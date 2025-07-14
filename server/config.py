"""Compatibility layer exporting :class:`Settings` as :class:`Config`."""

from .settings import Settings, ConfigError

Config = Settings

__all__ = ["Settings", "Config", "ConfigError"]
