from __future__ import annotations

import base64
import types

from fastapi.testclient import TestClient

from .db_utils import migrate_sqlite


class DummyStateManager:
    def create_session(self, *_, **__):
        pass

    def append_history(self, *_, **__):
        pass

    def get_summary(self, *_):
        return ""

    def is_escalation_required(self, *_):
        return False


class DummyAgent:
    async def generate_response(self, text: str, conversation_id: str, **_):
        yield types.SimpleNamespace(message=types.SimpleNamespace(text=f"echo:{text}"))


def test_chat_ws(monkeypatch, tmp_path):
    migrate_sqlite(monkeypatch, tmp_path)
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())

    from server import app as server_app
    from server.app import create_app
    from server.settings import Settings

    monkeypatch.setattr(server_app, "StateManager", lambda: DummyStateManager())
    monkeypatch.setattr(
        server_app, "build_core_agent", lambda *_: types.SimpleNamespace(agent=None)
    )
    monkeypatch.setattr(
        server_app, "SafeFunctionCallingAgent", lambda *_, **__: DummyAgent()
    )

    app = create_app(Settings())
    client = TestClient(app)

    with client.websocket_connect("/chat/ws") as ws:
        data = ws.receive_json()
        assert "session_id" in data
        ws.send_text("hello")
        resp = ws.receive_text()
        assert resp == "echo:hello"
