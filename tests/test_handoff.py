from __future__ import annotations

import pytest
import xml.etree.ElementTree as ET
import types
import os
import base64

from server.handoff import dial_twiml
from server import app as server_app  # noqa: E402
from server.settings import Settings
from .db_utils import migrate_sqlite
from fastapi.testclient import TestClient

from tests.utils.vocode_mocks import install as install_vocode

install_vocode()


os.environ.setdefault("SECRET_KEY", "x")
os.environ.setdefault("BASE_URL", "http://localhost")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "sid")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "token")
os.environ.setdefault("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())


def test_dial_twiml(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ESCALATION_PHONE_NUMBER", "+1234567890")
    xml = dial_twiml("+15551234567")
    root = ET.fromstring(xml)
    dial = root.find("Dial")
    assert dial is not None
    assert dial.text == "+1234567890"
    assert dial.attrib["callerId"] == "+15551234567"


def test_dial_twiml_no_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ESCALATION_PHONE_NUMBER", raising=False)
    with pytest.raises(RuntimeError):
        dial_twiml()


def test_inbound_call_escalation(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    db = migrate_sqlite(monkeypatch, tmp_path)
    key = db.create_api_key("tester")

    class DummyStateManager:
        def create_session(self, *args: object, **kwargs: object) -> None:
            pass

        def is_escalation_required(self, _: str) -> bool:
            return True

        def get_summary(self, _: str) -> str:
            return "summary"

    monkeypatch.setattr(server_app, "StateManager", lambda: DummyStateManager())
    monkeypatch.setattr(
        server_app,
        "build_core_agent",
        lambda *_, **__: types.SimpleNamespace(agent=None),
    )
    monkeypatch.setattr(
        server_app, "echo", types.SimpleNamespace(delay=lambda *a, **k: None)
    )

    sent: dict[str, str] = {}

    def fake_send_sms(to_phone: str, from_phone: str, body: str) -> None:
        sent["to"] = to_phone
        sent["from"] = from_phone
        sent["body"] = body

    monkeypatch.setattr("tools.notifications.send_sms", fake_send_sms)
    monkeypatch.setattr(server_app, "send_sms", fake_send_sms)
    monkeypatch.setenv("ESCALATION_PHONE_NUMBER", "+15550001111")
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())

    app = server_app.create_app(Settings())
    client = TestClient(app)

    resp = client.post(
        "/v1/inbound_call",
        data={"CallSid": "abc", "From": "+12025550100", "To": "+12025550199"},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 200
    assert sent == {
        "to": "+15550001111",
        "from": "+12025550100",
        "body": "summary",
    }


def test_inbound_call_validation(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())

    db_module = migrate_sqlite(monkeypatch, tmp_path)
    app = server_app.create_app(Settings())
    client = TestClient(app)
    key = db_module.create_api_key("tester")

    resp = client.post(
        "/v1/inbound_call",
        data={"From": "+1202555"},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"] == "invalid_request"
