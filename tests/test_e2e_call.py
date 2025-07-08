import os
import types
import sys
import base64
from importlib import reload
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

# Dummy vocode modules

dummy = types.ModuleType("vocode")
dummy.streaming = types.ModuleType("vocode.streaming")
dummy.streaming.agent = types.ModuleType("vocode.streaming.agent")
dummy.streaming.agent.chat_gpt_agent = types.ModuleType(
    "vocode.streaming.agent.chat_gpt_agent"
)
dummy.streaming.agent.base_agent = types.ModuleType("vocode.streaming.agent.base_agent")
dummy.streaming.agent.default_factory = types.ModuleType(
    "vocode.streaming.agent.default_factory"
)
dummy.streaming.telephony = types.ModuleType("vocode.streaming.telephony")
dummy.streaming.telephony.server = types.ModuleType("vocode.streaming.telephony.server")
dummy.streaming.telephony.server.base = types.ModuleType(
    "vocode.streaming.telephony.server.base"
)
dummy.streaming.telephony.config_manager = types.ModuleType(
    "vocode.streaming.telephony.config_manager"
)
dummy.streaming.telephony.config_manager.in_memory_config_manager = types.ModuleType(
    "vocode.streaming.telephony.config_manager.in_memory_config_manager"
)
dummy.streaming.models = types.ModuleType("vocode.streaming.models")
dummy.streaming.models.agent = types.ModuleType("vocode.streaming.models.agent")
dummy.streaming.models.actions = types.ModuleType("vocode.streaming.models.actions")
dummy.streaming.models.message = types.ModuleType("vocode.streaming.models.message")
dummy.streaming.models.transcriber = types.ModuleType(
    "vocode.streaming.models.transcriber"
)
dummy.streaming.models.synthesizer = types.ModuleType(
    "vocode.streaming.models.synthesizer"
)
dummy.streaming.models.telephony = types.ModuleType("vocode.streaming.models.telephony")


class Dummy:
    def __init__(self, *args: object, **kwargs: object) -> None:
        pass


dummy.streaming.agent.chat_gpt_agent.ChatGPTAgent = Dummy
dummy.streaming.agent.base_agent.AgentInput = Dummy
dummy.streaming.agent.base_agent.AgentResponseMessage = Dummy
dummy.streaming.agent.base_agent.GeneratedResponse = Dummy
dummy.streaming.agent.base_agent.BaseAgent = Dummy
dummy.streaming.agent.default_factory.DefaultAgentFactory = Dummy
dummy.streaming.models.agent.AgentConfig = Dummy
dummy.streaming.models.agent.ChatGPTAgentConfig = Dummy
dummy.streaming.models.actions.FunctionCall = Dummy
dummy.streaming.models.message.BaseMessage = Dummy
dummy.streaming.models.message.EndOfTurn = Dummy
dummy.streaming.models.transcriber.WhisperCPPTranscriberConfig = Dummy
dummy.streaming.models.synthesizer.ElevenLabsSynthesizerConfig = Dummy


class TelephonyServer:
    def __init__(self, *_: object, **__: object) -> None:
        pass

    def create_inbound_route(self, *_: object, **__: object):
        async def dummy_route(**___: object):
            return type(
                "Resp",
                (),
                {"body": b"", "status_code": 200, "media_type": "text/plain"},
            )

        return dummy_route


class TwilioInboundCallConfig:
    def __init__(self, **__: object) -> None:
        pass


class InMemoryConfigManager:
    pass


class TwilioConfig:
    def __init__(self, **__: object) -> None:
        pass


dummy.streaming.telephony.server.base.TelephonyServer = TelephonyServer
dummy.streaming.telephony.server.base.TwilioInboundCallConfig = TwilioInboundCallConfig
dummy.streaming.telephony.config_manager.in_memory_config_manager.InMemoryConfigManager = (
    InMemoryConfigManager
)
dummy.streaming.models.telephony.TwilioConfig = TwilioConfig

sys.modules["vocode"] = dummy
sys.modules["vocode.streaming"] = dummy.streaming
sys.modules["vocode.streaming.agent"] = dummy.streaming.agent
sys.modules[
    "vocode.streaming.agent.chat_gpt_agent"
] = dummy.streaming.agent.chat_gpt_agent
sys.modules["vocode.streaming.agent.base_agent"] = dummy.streaming.agent.base_agent
sys.modules[
    "vocode.streaming.agent.default_factory"
] = dummy.streaming.agent.default_factory
sys.modules["vocode.streaming.telephony"] = dummy.streaming.telephony
sys.modules["vocode.streaming.telephony.server"] = dummy.streaming.telephony.server
sys.modules[
    "vocode.streaming.telephony.server.base"
] = dummy.streaming.telephony.server.base
sys.modules[
    "vocode.streaming.telephony.config_manager"
] = dummy.streaming.telephony.config_manager
sys.modules[
    "vocode.streaming.telephony.config_manager.in_memory_config_manager"
] = dummy.streaming.telephony.config_manager.in_memory_config_manager
sys.modules["vocode.streaming.models"] = dummy.streaming.models
sys.modules["vocode.streaming.models.agent"] = dummy.streaming.models.agent
sys.modules["vocode.streaming.models.actions"] = dummy.streaming.models.actions
sys.modules["vocode.streaming.models.message"] = dummy.streaming.models.message
sys.modules["vocode.streaming.models.transcriber"] = dummy.streaming.models.transcriber
sys.modules["vocode.streaming.models.synthesizer"] = dummy.streaming.models.synthesizer
sys.modules["vocode.streaming.models.telephony"] = dummy.streaming.models.telephony

os.environ.setdefault("SECRET_KEY", "x")
os.environ.setdefault("BASE_URL", "http://localhost")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "your_auth_token")
os.environ.setdefault("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())

from server import app as server_app  # noqa: E402
from server import database as db  # noqa: E402
from server import recordings as rec  # noqa: E402
from server import tasks  # noqa: E402


def test_full_call_flow(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "your_auth_token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())
    monkeypatch.setenv("ESCALATION_PHONE_NUMBER", "+15550001111")
    reload(db)
    db.init_db()

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

    app = server_app.create_app()
    client = app.test_client()

    call_sid = "CA00000000000000000000000000000000"

    resp = client.post(
        "/inbound_call",
        data={"CallSid": call_sid, "From": "+15005550006", "To": "+15005550010"},
    )
    assert resp.status_code == 200

    resp = client.post(
        "/recording_status",
        data={
            "CallSid": call_sid,
            "RecordingSid": "RS0000000000",
            "RecordingUrl": "http://twilio.test/record",
        },
    )
    assert resp.status_code == 204

    path = rec.download_recording(
        "http://twilio.test/record",
        auth=(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"]),
    )
    result = tasks.transcribe_audio(str(path), call_sid, "+15005550006", "+15005550010")

    assert sent == {"to": "+15550001111", "from": "+15005550006", "body": "summary"}
    assert Path(result).exists()
    assert transcript_path.exists()

    with db.get_session() as session:
        call = session.query(db.Call).filter_by(call_sid=call_sid).one()
        assert call.summary
