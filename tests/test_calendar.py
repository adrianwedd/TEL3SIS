from __future__ import annotations

from datetime import datetime, timedelta, UTC
from typing import Any
import types
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import pytest

import fakeredis

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools.calendar import (
    create_event,
    list_events,
    AuthError,
    _get_credentials,
    exchange_code,
)
from google.auth.exceptions import RefreshError
from server.state_manager import StateManager


class DummyInsert:
    def __init__(self) -> None:
        self.body = None

    def execute(self, **_: Any) -> dict:
        return {"id": "evt"}


class DummyList:
    def __init__(self) -> None:
        self.kwargs: dict[str, Any] = {}

    def execute(self, **_: Any) -> dict:
        return {"items": [{"id": "evt"}]}


class DummyEvents:
    def insert(self, calendarId: str, body: dict) -> DummyInsert:  # noqa: ANN001
        self.body = body
        return DummyInsert()

    def list(self, **kwargs: Any) -> DummyList:
        dl = DummyList()
        dl.kwargs = kwargs
        return dl


class DummyService:
    def __init__(self) -> None:
        self._events = DummyEvents()

    def events(self) -> DummyEvents:
        return self._events


def _make_manager(monkeypatch: Any) -> StateManager:
    key = AESGCM.generate_key(bit_length=128)
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(key).decode())
    monkeypatch.setenv("VECTOR_DB_PATH", "vector")
    monkeypatch.setenv("EMBEDDING_MODEL_NAME", "dummy-model")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("SENDGRID_API_KEY", "sg")
    monkeypatch.setenv("SENDGRID_FROM_EMAIL", "from@test")
    monkeypatch.setenv("NOTIFY_EMAIL", "notify@test")

    class DummyModel:
        def __init__(self, name: str) -> None:
            self.name = name

        def encode(self, texts: list[str]):  # noqa: ANN001
            import numpy as np

            return np.zeros((len(texts), 2))

    monkeypatch.setattr("server.vector_db.SentenceTransformer", DummyModel)
    manager = StateManager(url="redis://localhost:6379/0")
    manager._redis = fakeredis.FakeRedis(decode_responses=True)
    manager.set_token("user", "tok", "rt", expires_at=9999999999)
    return manager


def _patch_build(monkeypatch: Any, service: DummyService) -> None:
    def fake_build(
        service_name: str, version: str, credentials: Any, **_: Any
    ) -> DummyService:  # noqa: ANN001
        assert service_name == "calendar"
        assert version == "v3"
        return service

    monkeypatch.setattr("tools.calendar.build", fake_build)


def test_create_and_list_events(monkeypatch: Any) -> None:
    manager = _make_manager(monkeypatch)
    service = DummyService()
    _patch_build(monkeypatch, service)

    start = datetime.now(UTC)
    end = start + timedelta(hours=1)

    result = create_event(manager, "user", "Meeting", start, end)
    assert result["id"] == "evt"
    assert service._events.body["summary"] == "Meeting"

    events = list_events(manager, "user", start, end)
    assert events == [{"id": "evt"}]


def test_auth_failure_triggers_sms(monkeypatch: Any) -> None:
    manager = _make_manager(monkeypatch)
    manager.delete_token("user")

    sent: dict[str, Any] = {}

    def fake_send_sms(to: str, from_: str, body: str) -> None:  # noqa: ANN001
        sent["to"] = to
        sent["from"] = from_
        sent["body"] = body

    monkeypatch.setattr("tools.calendar.send_sms", fake_send_sms)
    monkeypatch.setattr("tools.calendar.generate_auth_url", lambda *_: "link")

    with pytest.raises(AuthError):
        create_event(
            manager,
            "user",
            "Meeting",
            datetime.now(UTC),
            datetime.now(UTC),
            user_phone="123",
            twilio_phone="456",
        )
    assert sent["to"] == "123"
    assert "link" in sent["body"]


def test_get_credentials_refreshes(monkeypatch: Any) -> None:
    manager = _make_manager(monkeypatch)
    expires = int((datetime.now(UTC) - timedelta(minutes=1)).timestamp())
    manager.set_token("user", "old", "rt", expires_at=expires)

    class DummyCreds:
        def __init__(
            self,
            token,
            refresh_token=None,
            token_uri=None,
            client_id=None,
            client_secret=None,
        ):  # noqa: ANN001
            self.token = token
            self.refresh_token = refresh_token
            self.expiry = datetime.now(UTC)
            self.expired = True

        calls = 0

        def refresh(self, request, **kwargs: Any):  # noqa: ANN001
            DummyCreds.calls += 1
            if DummyCreds.calls < 2:
                raise Exception("boom")
            self.token = "new"
            self.expiry = datetime.now(UTC) + timedelta(hours=1)

    monkeypatch.setattr("tools.calendar.Credentials", DummyCreds)
    monkeypatch.setattr("tools.calendar.Request", lambda: None)

    creds = _get_credentials(manager, "user")
    assert creds.token == "new"
    data = manager.get_token("user")
    assert data["access_token"] == "new"
    assert DummyCreds.calls == 2


def test_get_credentials_refresh_failure(monkeypatch: Any) -> None:
    manager = _make_manager(monkeypatch)
    expires = int((datetime.now(UTC) - timedelta(minutes=1)).timestamp())
    manager.set_token("user", "old", "rt", expires_at=expires)

    class DummyCreds:
        def __init__(
            self,
            token,
            refresh_token=None,
            token_uri=None,
            client_id=None,
            client_secret=None,
        ):
            self.token = token
            self.refresh_token = refresh_token
            self.expiry = datetime.now(UTC)
            self.expired = True

        def refresh(self, request, **kwargs: Any):
            raise RefreshError("denied")

    sent: dict[str, Any] = {}

    def fake_send_sms(to: str, from_: str, body: str) -> None:
        sent["to"] = to
        sent["from"] = from_
        sent["body"] = body

    monkeypatch.setattr("tools.calendar.Credentials", DummyCreds)
    monkeypatch.setattr("tools.calendar.Request", lambda: None)
    monkeypatch.setattr("tools.calendar.generate_auth_url", lambda *_: "link")
    monkeypatch.setattr("tools.calendar.send_sms", fake_send_sms)

    with pytest.raises(AuthError):
        _get_credentials(
            manager,
            "user",
            user_phone="123",
            twilio_phone="456",
        )

    assert sent["to"] == "123"
    assert "link" in sent["body"]


def test_create_event_network_failure(monkeypatch: Any) -> None:
    manager = _make_manager(monkeypatch)

    def fail_build(*args, **kwargs):  # noqa: ANN001, ARG001
        raise RuntimeError("network")

    monkeypatch.setattr("tools.calendar.build", fail_build)

    start = datetime.now(UTC)
    end = start + timedelta(hours=1)
    result = create_event(manager, "user", "Meeting", start, end)
    assert result["error"].startswith("Sorry")


def test_list_events_network_failure(monkeypatch: Any) -> None:
    manager = _make_manager(monkeypatch)

    def fail_build(*args, **kwargs):  # noqa: ANN001, ARG001
        raise RuntimeError("network")

    monkeypatch.setattr("tools.calendar.build", fail_build)

    start = datetime.now(UTC)
    end = start + timedelta(hours=1)
    result = list_events(manager, "user", start, end)
    assert result == []


def test_exchange_code_retries(monkeypatch: Any) -> None:
    manager = _make_manager(monkeypatch)
    manager.set_oauth_state("state", "user")

    class DummyFlow:
        def __init__(self) -> None:
            self.calls = 0
            self.credentials = types.SimpleNamespace(
                token="tok",
                refresh_token="rt",
                expiry=datetime.now(UTC),
            )

        def authorization_url(self, access_type: str, include_granted_scopes: str):
            return "url", "state"

        def fetch_token(self, authorization_response: str, timeout: int = 10):
            self.calls += 1
            if self.calls < 2:
                raise Exception("boom")

    def fake_build_flow(state: str) -> DummyFlow:  # noqa: ANN001
        assert state == "state"
        return flow

    flow = DummyFlow()
    monkeypatch.setattr("tools.calendar._build_flow", fake_build_flow)

    exchange_code(manager, "state", "resp")
    data = manager.get_token("user")
    assert data["access_token"] == "tok"
    assert flow.calls == 2
