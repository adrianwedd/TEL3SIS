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
    openai_embedding_model: str = field(
        default_factory=lambda: os.environ.get(
            "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
        )
    )
    openai_api_key: str = field(
        default_factory=lambda: os.environ.get("OPENAI_API_KEY", "")
    )
    eleven_labs_api_key: str = field(
        default_factory=lambda: os.environ.get("ELEVEN_LABS_API_KEY", "")
    )
    celery_broker_url: str = field(
        default_factory=lambda: os.environ.get(
            "CELERY_BROKER_URL", os.environ.get("REDIS_URL", "redis://redis:6379/0")
        )
    )
    celery_result_backend: str = field(
        default_factory=lambda: os.environ.get(
            "CELERY_RESULT_BACKEND",
            os.environ.get(
                "CELERY_BROKER_URL", os.environ.get("REDIS_URL", "redis://redis:6379/0")
            ),
        )
    )
    token_encryption_key: str = field(
        default_factory=lambda: os.environ.get("TOKEN_ENCRYPTION_KEY", "")
    )
    google_client_id: str = field(
        default_factory=lambda: os.environ.get("GOOGLE_CLIENT_ID", "")
    )
    google_client_secret: str = field(
        default_factory=lambda: os.environ.get("GOOGLE_CLIENT_SECRET", "")
    )
    escalation_phone_number: str = field(
        default_factory=lambda: os.environ.get("ESCALATION_PHONE_NUMBER", "")
    )
    call_rate_limit: str = field(
        default_factory=lambda: os.environ.get("CALL_RATE_LIMIT", "3/minute")
    )
    api_rate_limit: str = field(
        default_factory=lambda: os.environ.get("API_RATE_LIMIT", "60/minute")
    )
    oauth_auth_url: str = field(
        default_factory=lambda: os.environ.get(
            "OAUTH_AUTH_URL", "https://example.com/auth"
        )
    )
    vector_db_path: str = field(
        default_factory=lambda: os.environ.get("VECTOR_DB_PATH", "vector_store")
    )
    backup_dir: str = field(
        default_factory=lambda: os.environ.get("BACKUP_DIR", "backups")
    )
    backup_s3_bucket: str = field(
        default_factory=lambda: os.environ.get("BACKUP_S3_BUCKET", "")
    )
    openai_model: str = field(
        default_factory=lambda: os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
    )
    openai_safety_model: str = field(
        default_factory=lambda: os.environ.get("OPENAI_SAFETY_MODEL", "gpt-3.5-turbo")
    )
    log_level: str = field(default_factory=lambda: os.environ.get("LOG_LEVEL", "INFO"))
    log_rotation: str = field(
        default_factory=lambda: os.environ.get("LOG_ROTATION", "10 MB")
    )
    log_file: str = field(
        default_factory=lambda: os.environ.get("LOG_FILE", "logs/tel3sis.log")
    )
    slack_webhook_url: str = field(
        default_factory=lambda: os.environ.get("SLACK_WEBHOOK_URL", "")
    )

    def __post_init__(self) -> None:
        required = [
            "secret_key",
            "base_url",
            "twilio_account_sid",
            "twilio_auth_token",
        ]
        missing = [name for name in required if not getattr(self, name)]
        if missing:
            raise ConfigError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
