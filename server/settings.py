"""Application settings loaded from environment variables."""
from __future__ import annotations

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigError(RuntimeError):
    """Raised when required environment variables are missing."""


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    secret_key: str
    base_url: str
    twilio_account_sid: str
    twilio_auth_token: str

    sendgrid_api_key: str = ""
    sendgrid_from_email: str = ""
    notify_email: str = ""
    redis_url: str = "redis://redis:6379/0"
    database_url: str = "sqlite:///tel3sis.db"
    embedding_provider: str = "sentence_transformers"
    embedding_model_name: str = "all-MiniLM-L6-v2"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_api_key: str = ""
    eleven_labs_api_key: str = ""
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None
    token_encryption_key: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    escalation_phone_number: str = ""
    call_rate_limit: str = "3/minute"
    api_rate_limit: str = "60/minute"
    oauth_auth_url: str = "https://example.com/auth"
    vector_db_path: str = "vector_store"
    backup_dir: str = "backups"
    backup_s3_bucket: str = ""
    openai_model: str = "gpt-3.5-turbo"
    openai_safety_model: str = "gpt-3.5-turbo"
    log_level: str = "INFO"
    log_rotation: str = "10 MB"
    log_file: str = "logs/tel3sis.log"
    slack_webhook_url: str = ""
    use_fake_services: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def __init__(self, **data: object) -> None:
        try:
            super().__init__(**data)
        except ValidationError as exc:
            raise ConfigError(str(exc)) from exc

    def model_post_init(
        self, __context: dict[str, object] | None
    ) -> None:  # noqa: D401
        if self.celery_broker_url is None:
            self.celery_broker_url = self.redis_url
        if self.celery_result_backend is None:
            self.celery_result_backend = self.celery_broker_url

    @classmethod
    def load(cls) -> "Settings":
        """Return settings loaded from environment or raise ``ConfigError``."""
        try:
            return cls()  # type: ignore[call-arg]
        except ValidationError as exc:  # pragma: no cover - pydantic formatting
            raise ConfigError(str(exc)) from exc


# Backwards compatibility
Config = Settings

__all__ = ["Settings", "Config", "ConfigError"]
