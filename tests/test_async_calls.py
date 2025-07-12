import base64
import types


# Reuse dummy vocode modules from test_api_key_auth
import tests.test_api_key_auth  # noqa: F401
from fastapi.testclient import TestClient

from .db_utils import migrate_sqlite


def test_async_inbound_call(monkeypatch, tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())
    db = migrate_sqlite(monkeypatch, tmp_path)
    key = db.create_api_key("tester")

    from server import app as server_app
    from server.app import create_app
    from server.config import Config

    class DummyStateManager:
        def create_session(self, *a, **k):
            pass

        def is_escalation_required(self, *_: object) -> bool:
            return False

        def get_summary(self, *_: object) -> str:
            return ""

    monkeypatch.setattr(server_app, "StateManager", lambda: DummyStateManager())

    monkeypatch.setattr(
        server_app,
        "build_core_agent",
        lambda *_, **__: types.SimpleNamespace(agent=None),
    )
    monkeypatch.setattr(
        server_app, "echo", types.SimpleNamespace(delay=lambda *_, **__: None)
    )

    app = create_app(Config())
    client = TestClient(app)
    resp = client.post(
        "/v1/inbound_call",
        data={"CallSid": "CA1", "From": "+12025550100", "To": "+12025550101"},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 200


def test_async_recording_status(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())
    from server import app as server_app
    from server.app import create_app
    from server.config import Config

    monkeypatch.setattr(server_app, "verify_api_key", lambda *_: True)

    app = create_app(Config())
    client = TestClient(app)
    resp = client.post(
        "/v1/recording_status",
        data={
            "CallSid": "CA1",
            "RecordingSid": "RS1",
            "RecordingUrl": "http://example.com",
        },
        headers={"X-API-Key": "dummy"},
    )
    assert resp.status_code == 204
