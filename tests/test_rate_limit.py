import types
import sys
import os
import base64
import fakeredis
from importlib import reload

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
os.environ.setdefault("TWILIO_ACCOUNT_SID", "sid")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "token")
os.environ.setdefault("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())

from server import database as db  # noqa: E402
import server.state_manager as sm  # noqa: E402


def test_rate_limits(monkeypatch, tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("CALL_RATE_LIMIT", "1/minute")
    monkeypatch.setenv("API_RATE_LIMIT", "1/minute")
    monkeypatch.setenv("RATE_LIMIT_REDIS_URL", "memory://")
    reload(db)
    db.init_db()
    key = db.create_api_key("tester")

    monkeypatch.setattr(sm, "redis", types.SimpleNamespace(Redis=fakeredis.FakeRedis))

    from server.app import create_app  # noqa: E402
    import server.app as server_app  # noqa: E402
    from fastapi.testclient import TestClient

    monkeypatch.setattr(
        server_app,
        "build_core_agent",
        lambda *_, **__: types.SimpleNamespace(agent=None),
    )
    monkeypatch.setattr(
        server_app, "echo", types.SimpleNamespace(delay=lambda *a, **k: None)
    )

    app = create_app()
    client = TestClient(app)

    resp = client.get("/v1/calls", headers={"X-API-Key": key})
    assert resp.status_code == 200
    resp = client.get("/v1/calls", headers={"X-API-Key": key})
    assert resp.status_code == 429

    resp = client.post(
        "/v1/inbound_call",
        data={"CallSid": "1", "From": "+1", "To": "+2"},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 200
    resp = client.post(
        "/v1/inbound_call",
        data={"CallSid": "2", "From": "+1", "To": "+2"},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 429
