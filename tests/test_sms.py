import base64

import pytest
from fastapi.testclient import TestClient

from tests.utils.vocode_mocks import install as install_vocode
from tests.db_utils import migrate_sqlite
from server import app as server_app
from server.config import Config

install_vocode()


def _setup(monkeypatch: pytest.MonkeyPatch, tmp_path):
    db = migrate_sqlite(monkeypatch, tmp_path)
    key = db.create_api_key("tester")
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())

    class DummyStateManager:
        def create_session(self, *_: object, **__: object) -> None:
            pass

    monkeypatch.setattr(server_app, "StateManager", lambda: DummyStateManager())
    return key


def test_inbound_sms(monkeypatch: pytest.MonkeyPatch, tmp_path):
    key = _setup(monkeypatch, tmp_path)

    sent = {}

    def fake_send_sms(to: str, from_: str, body: str) -> None:
        sent["to"] = to
        sent["from"] = from_
        sent["body"] = body

    class DummyAgent:
        def __init__(self, *_: object, **__: object) -> None:
            pass

        async def handle_message(self, text: str) -> str:
            return f"echo:{text}"

    monkeypatch.setattr("tools.notifications.send_sms", fake_send_sms)
    monkeypatch.setattr(server_app, "send_sms", fake_send_sms)
    monkeypatch.setattr(server_app, "SMSAgent", DummyAgent)

    app = server_app.create_app(Config())
    client = TestClient(app)

    resp = client.post(
        "/v1/inbound_sms",
        data={"MessageSid": "SM1", "From": "+1", "To": "+2", "Body": "hi"},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 204
    assert sent == {"to": "+1", "from": "+2", "body": "echo:hi"}


def test_inbound_sms_validation(monkeypatch: pytest.MonkeyPatch, tmp_path):
    key = _setup(monkeypatch, tmp_path)

    app = server_app.create_app(Config())
    client = TestClient(app)

    resp = client.post(
        "/v1/inbound_sms",
        data={"From": "+1"},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "invalid_request"
