import os
import types
import sys
import base64
from pathlib import Path

import pytest
from .db_utils import migrate_sqlite
from server import database as db
from server import app as server_app
from server import recordings as rec
from server import tasks
from server.settings import Settings
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tests.utils.vocode_mocks import install as install_vocode

install_vocode()

os.environ.setdefault("SECRET_KEY", "x")
os.environ.setdefault("BASE_URL", "http://localhost")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "your_auth_token")
os.environ.setdefault("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())


def test_full_call_flow(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "your_auth_token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())
    monkeypatch.setenv("ESCALATION_PHONE_NUMBER", "+15550001111")
    db_module = migrate_sqlite(monkeypatch, tmp_path)
    key = db_module.create_api_key("tester")

    class DummyStateManager:
        def create_session(self, *_: object, **__: object) -> None:
            pass

        def is_escalation_required(self, __: str) -> bool:
            return True

        def get_summary(self, __: str) -> str:
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

    audio_path = tmp_path / "audio" / "call.mp3"

    def fake_download_recording(
        url: str, *, output_dir: Path = tmp_path / "audio", auth: tuple[str, str]
    ) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_path.write_bytes(b"sound")
        return audio_path

    monkeypatch.setattr(rec, "download_recording", fake_download_recording)

    transcript_path = tmp_path / "transcripts" / "call.txt"

    def fake_transcribe_recording(
        _path: Path,
        *,
        output_dir: Path = tmp_path / "transcripts",
        model_name: str = "base",
    ) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        transcript_path.write_text("hello world")
        return transcript_path

    monkeypatch.setattr(rec, "transcribe_recording", fake_transcribe_recording)
    monkeypatch.setattr(tasks, "transcribe_recording", fake_transcribe_recording)
    monkeypatch.setattr(
        tasks,
        "send_transcript_email",
        types.SimpleNamespace(delay=lambda *_, **__: None),
    )
    monkeypatch.setattr(tasks, "generate_self_critique", lambda *_: "crit")

    def fake_process(url: str, call_id: str, f: str, t: str) -> str:
        audio = rec.download_recording(
            url, output_dir=tmp_path / "audio", auth=("sid", "token")
        )
        return tasks.transcribe_audio(str(audio), call_id, f, t)

    monkeypatch.setattr(
        server_app,
        "process_recording",
        types.SimpleNamespace(delay=fake_process),
    )

    app = server_app.create_app(Settings())
    client = TestClient(app)

    call_sid = "CA00000000000000000000000000000000"

    resp = client.post(
        "/v1/inbound_call",
        data={"CallSid": call_sid, "From": "+15005550006", "To": "+15005550010"},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 200

    resp = client.post(
        "/v1/recording_status",
        data={
            "CallSid": call_sid,
            "RecordingSid": "RS0000000000",
            "RecordingUrl": "http://twilio.test/record",
        },
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 204

    assert sent == {"to": "+15550001111", "from": "+15005550006", "body": "summary"}
    assert transcript_path.exists()

    with db_module.get_session() as session:
        call = session.query(db_module.Call).filter_by(call_sid=call_sid).one()
        assert call.summary


def test_recording_status_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    from server import app as server_app
    from server.settings import Settings

    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())

    app = server_app.create_app(Settings())
    client = TestClient(app)
    key = db.create_api_key("tester")

    resp = client.post(
        "/v1/recording_status",
        data={"CallSid": "abc"},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "invalid_request"
