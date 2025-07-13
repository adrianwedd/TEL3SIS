from __future__ import annotations

import base64
import types
from importlib import reload
from pathlib import Path

import pytest
from .db_utils import migrate_sqlite

from tests.utils.vocode_mocks import install as install_vocode

install_vocode()


from server import app as server_app  # noqa: E402
from server.settings import Settings  # noqa: E402
from server import tasks  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from tools import language  # noqa: E402


def _setup_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[str, object]:
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())

    db_module = migrate_sqlite(monkeypatch, tmp_path)
    reload(tasks)
    key = db_module.create_api_key("tester")
    return key, db_module


def test_language_switch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    key, db_module = _setup_env(monkeypatch, tmp_path)

    class DummyStateManager:
        def create_session(self, *_, **__):
            pass

        def update_session(self, *_, **__):
            pass

        def is_escalation_required(self, _sid: str) -> bool:
            return False

        def get_summary(self, _sid: str) -> str:
            return ""

    monkeypatch.setattr(server_app, "StateManager", lambda: DummyStateManager())
    monkeypatch.setattr(
        server_app, "echo", types.SimpleNamespace(delay=lambda *a, **k: None)
    )

    captured: dict[str, str] = {}

    def fake_build_core_agent(_sm: object, _sid: object = None, language: str = "en"):
        captured["lang"] = language
        return types.SimpleNamespace(agent=None)

    monkeypatch.setattr(server_app, "build_core_agent", fake_build_core_agent)

    app = server_app.create_app(Settings())
    client = TestClient(app)

    from_num = "+15005550006"
    to_num = "+15005550010"

    monkeypatch.setattr(language, "guess_language_from_number", lambda *_: "fr")

    resp = client.post(
        "/v1/inbound_call",
        data={"CallSid": "CA1", "From": from_num, "To": to_num},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 200
    assert captured["lang"] == "fr"
    assert db_module.get_user_preference(from_num, "language") == "fr"

    transcript = tmp_path / "call.txt"
    transcript.write_text("hola mundo")

    monkeypatch.setattr(tasks, "transcribe_recording", lambda *a, **k: transcript)
    monkeypatch.setattr(
        tasks,
        "send_transcript_email",
        types.SimpleNamespace(delay=lambda *a, **k: None),
    )
    monkeypatch.setattr(tasks, "generate_self_critique", lambda *_: "")
    monkeypatch.setattr(tasks, "summarize_text", lambda t: "sum")
    monkeypatch.setattr(tasks, "detect_language", lambda t: "es")

    tasks.transcribe_audio(str(transcript), "CA1", from_num, to_num)

    assert db_module.get_user_preference(from_num, "language") == "es"

    captured.clear()
    resp = client.post(
        "/v1/inbound_call",
        data={"CallSid": "CA2", "From": from_num, "To": to_num},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 200
    assert captured["lang"] == "es"


def test_guess_language_from_number() -> None:
    assert language.guess_language_from_number("+341234") == "es"
    assert language.guess_language_from_number("+1555") == "en"
