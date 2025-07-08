from __future__ import annotations

import os
from dataclasses import dataclass, field


class ConfigError(RuntimeError):
    """Raised when required environment variables are missing."""


@dataclass
class Config:
    """Application configuration loaded from environment variables."""

    secret_key: str = field(default_factory=lambda: os.environ.get("SECRET_KEY", ""))
    base_url: str = field(default_factory=lambda: os.environ.get("BASE_URL", ""))
    twilio_account_sid: str = field(
        default_factory=lambda: os.environ.get("TWILIO_ACCOUNT_SID", "")
    )
    twilio_auth_token: str = field(
        default_factory=lambda: os.environ.get("TWILIO_AUTH_TOKEN", "")
    )

    def __post_init__(self) -> None:
        missing = [name for name, value in self.__dict__.items() if not value]
        if missing:
            raise ConfigError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
