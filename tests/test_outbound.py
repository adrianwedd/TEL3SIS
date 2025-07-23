import base64
import pytest
from fastapi.testclient import TestClient

from tests.utils.vocode_mocks import install as install_vocode
from tests.db_utils import migrate_sqlite
from server import app as server_app
from server.settings import Settings

install_vocode()


def _setup(monkeypatch: pytest.MonkeyPatch, tmp_path):
    db = migrate_sqlite(monkeypatch, tmp_path)
    key = db.create_api_key("tester")
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())
    monkeypatch.setenv("TWILIO_PHONE_NUMBER", "+15550009999")
    return key


def test_send_sms_api(monkeypatch: pytest.MonkeyPatch, tmp_path):
    key = _setup(monkeypatch, tmp_path)
    sent = {}

    def fake_send_sms(to: str, from_: str, body: str) -> None:
        sent["args"] = (to, from_, body)

    monkeypatch.setattr(server_app, "send_sms", fake_send_sms)

    app = server_app.create_app(Settings())
    client = TestClient(app)

    resp = client.post(
        "/v1/send_sms",
        json={"to": "+1", "body": "hi"},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 204
    assert sent["args"] == ("+1", "+15550009999", "hi")


def test_outbound_call_api(monkeypatch: pytest.MonkeyPatch, tmp_path):
    key = _setup(monkeypatch, tmp_path)
    called = {}

    def fake_start_call(to: str, from_: str, url: str) -> None:
        called["args"] = (to, from_, url)

    monkeypatch.setattr(server_app, "start_call", fake_start_call)

    app = server_app.create_app(Settings())
    client = TestClient(app)

    resp = client.post(
        "/v1/outbound_call",
        json={"to": "+1"},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 202
    assert called["args"][0] == "+1"
    assert called["args"][1] == "+15550009999"
    assert called["args"][2].endswith("/v1/inbound_call")
