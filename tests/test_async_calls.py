import base64
import types


# Reuse dummy vocode modules from test_api_key_auth
import tests.test_api_key_auth  # noqa: F401
import pytest
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
    from server.settings import Settings

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

    app = create_app(Settings())
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
    from server.settings import Settings

    monkeypatch.setattr(server_app, "verify_api_key", lambda *_: True)

    class DummyStateManager:
        def create_session(self, *_: object, **__: object) -> None:
            pass

        def get_session(self, *_: object) -> dict[str, str]:
            return {}

        def is_escalation_required(self, *_: object) -> bool:
            return False

        def get_summary(self, *_: object) -> str:
            return ""

    monkeypatch.setattr(server_app, "StateManager", lambda: DummyStateManager())

    called: dict[str, tuple] = {}

    def fake_process(url: str, sid: str, f: str, t: str) -> None:
        called["args"] = (url, sid, f, t)

    monkeypatch.setattr(
        server_app,
        "process_recording",
        types.SimpleNamespace(delay=fake_process),
    )

    app = create_app(Settings())
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
    assert called["args"] == ("http://example.com", "CA1", "", "")


def test_task_invocation_counter(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")

    import server.tasks as tasks

    before = tasks.task_invocations.labels("echo")._value.get()
    tasks.echo.run("hi")
    after = tasks.task_invocations.labels("echo")._value.get()

    assert after == before + 1


def test_task_failure_counter(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")

    import server.tasks as tasks

    def fail() -> None:
        with tasks.monitor_task("dummy"):
            raise RuntimeError("boom")

    inv_before = tasks.task_invocations.labels("dummy")._value.get()
    fail_before = tasks.task_failures.labels("dummy")._value.get()

    with pytest.raises(RuntimeError):
        fail()

    inv_after = tasks.task_invocations.labels("dummy")._value.get()
    fail_after = tasks.task_failures.labels("dummy")._value.get()

    assert inv_after == inv_before + 1
    assert fail_after == fail_before + 1
