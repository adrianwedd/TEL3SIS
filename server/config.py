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
    sendgrid_api_key: str = field(
        default_factory=lambda: os.environ.get("SENDGRID_API_KEY", "")
    )
    sendgrid_from_email: str = field(
        default_factory=lambda: os.environ.get("SENDGRID_FROM_EMAIL", "")
    )
    notify_email: str = field(
        default_factory=lambda: os.environ.get("NOTIFY_EMAIL", "")
    )
    redis_url: str = field(
        default_factory=lambda: os.environ.get("REDIS_URL", "redis://redis:6379/0")
    )
    database_url: str = field(
        default_factory=lambda: os.environ.get("DATABASE_URL", "sqlite:///tel3sis.db")
    )
    embedding_provider: str = field(
        default_factory=lambda: os.environ.get(
            "EMBEDDING_PROVIDER", "sentence_transformers"
        )
    )
    embedding_model_name: str = field(
        default_factory=lambda: os.environ.get(
            "EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2"
        )
    )

    def __post_init__(self) -> None:
        missing = [name for name, value in self.__dict__.items() if not value]
        if missing:
            raise ConfigError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
