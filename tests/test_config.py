import os
import base64
import pytest

from tests.utils.vocode_mocks import install as install_vocode

install_vocode()

# Dummy modules to allow importing server.app without dependencies


os.environ.setdefault("SECRET_KEY", "x")
os.environ.setdefault("BASE_URL", "http://localhost")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "sid")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "token")
os.environ.setdefault("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())


from server.settings import Settings, ConfigError  # noqa: E402
from server.app import create_app  # noqa: E402


def test_config_missing_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("BASE_URL", raising=False)
    monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)
    monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)
    with pytest.raises(ConfigError):
        Settings()


def test_create_app_missing_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("BASE_URL", raising=False)
    monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)
    monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)
    with pytest.raises(RuntimeError):
        create_app(Settings())


def test_create_app_missing_token_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TOKEN_ENCRYPTION_KEY", raising=False)
    with pytest.raises(RuntimeError):
        create_app(Settings())


def test_create_app_invalid_token_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"abc").decode())
    with pytest.raises(RuntimeError):
        create_app(Settings())


def test_config_embedding_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EMBEDDING_MODEL_NAME", "test-model")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    cfg = Settings()
    assert cfg.embedding_model_name == "test-model"
    assert cfg.embedding_provider == "openai"
