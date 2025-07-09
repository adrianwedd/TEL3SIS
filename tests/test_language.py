from __future__ import annotations

import base64
import sys
import types
from importlib import reload
from pathlib import Path

import pytest

# Dummy vocode modules for server import

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


dummy.streaming.telephony.server.base.TelephonyServer = Dummy
dummy.streaming.telephony.server.base.TwilioInboundCallConfig = Dummy
dummy.streaming.telephony.config_manager.in_memory_config_manager.InMemoryConfigManager = (
    Dummy
)
dummy.streaming.models.telephony.TwilioConfig = Dummy

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


from server import app as server_app  # noqa: E402
from server import tasks  # noqa: E402
from server import database as db  # noqa: E402
from tools import language  # noqa: E402


def _setup_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())

    reload(db)
    db.init_db()


def test_language_switch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _setup_env(monkeypatch, tmp_path)

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

    app = server_app.create_app()
    client = app.test_client()

    from_num = "+15005550006"
    to_num = "+15005550010"

    monkeypatch.setattr(language, "guess_language_from_number", lambda *_: "fr")

    resp = client.post(
        "/v1/inbound_call",
        data={"CallSid": "CA1", "From": from_num, "To": to_num},
    )
    assert resp.status_code == 200
    assert captured["lang"] == "fr"

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

    assert db.get_user_preference(from_num, "language") == "es"

    captured.clear()
    resp = client.post(
        "/v1/inbound_call",
        data={"CallSid": "CA2", "From": from_num, "To": to_num},
    )
    assert resp.status_code == 200
    assert captured["lang"] == "es"


def test_guess_language_from_number() -> None:
    assert language.guess_language_from_number("+341234") == "es"
    assert language.guess_language_from_number("+1555") == "en"
