import types

# ruff: noqa: E402
import sys
import os
import base64
from flask import Flask, session
from flask_login import LoginManager, login_user, UserMixin

# Stub chromadb and vocode dependencies
chroma = types.ModuleType("chromadb")


class _DummyCollection:
    def add(self, **_: object) -> None:
        pass

    def query(self, **_: object):
        return {"documents": [[]]}


class _DummyClient:
    def __init__(self, *_: object, **__: object) -> None:
        pass

    def get_or_create_collection(self, *_: object, **__: object):
        return _DummyCollection()

    def heartbeat(self) -> int:
        return 1


chroma.PersistentClient = _DummyClient
sys.modules["chromadb"] = chroma
sys.modules["chromadb.api"] = types.ModuleType("chromadb.api")
sys.modules["chromadb.api.types"] = types.SimpleNamespace(
    EmbeddingFunction=object, Embeddings=list
)

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

from server.dashboard_bp import bp, delete_call, reprocess_call
import pytest
from werkzeug.exceptions import Forbidden
from tests.db_utils import migrate_sqlite


class DummyUser(UserMixin):
    def __init__(self, role: str) -> None:
        self.id = 1
        self.role = role


def _setup_app(role: str) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "x"
    app.register_blueprint(bp)
    login_manager = LoginManager(app)

    @login_manager.user_loader
    def load_user(_id: str):  # pragma: no cover - required by LoginManager
        return DummyUser(role)

    return app


def test_delete_call_admin(monkeypatch, tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("SECRET_KEY", "x")
    db = migrate_sqlite(monkeypatch, tmp_path)
    db.create_user("admin", "pass", role="admin")

    tdir = tmp_path / "transcripts"
    tdir.mkdir()
    transcript = tdir / "t.txt"
    transcript.write_text("hi")

    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    monkeypatch.setattr("server.dashboard_bp.DEFAULT_OUTPUT_DIR", audio_dir)
    audio = audio_dir / "t.mp3"
    audio.write_text("a")

    db.save_call_summary("sid", "111", "222", str(transcript), "s", None)

    app = _setup_app("admin")
    with app.test_request_context(
        "/v1/calls/1/delete", method="POST", data={"csrf_token": "tok"}
    ):
        login_user(DummyUser("admin"))
        session["csrf_token"] = "tok"
        resp = delete_call(1)

    assert resp.status_code == 302
    assert not transcript.exists()
    assert not audio.exists()
    with db.get_session() as sess:
        assert not sess.query(db.Call).all()


def test_delete_call_forbidden(monkeypatch, tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("SECRET_KEY", "x")
    db = migrate_sqlite(monkeypatch, tmp_path)
    db.create_user("user", "pass", role="user")
    tdir = tmp_path / "transcripts"
    tdir.mkdir()
    transcript = tdir / "t.txt"
    transcript.write_text("hi")
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    monkeypatch.setattr("server.dashboard_bp.DEFAULT_OUTPUT_DIR", audio_dir)
    audio = audio_dir / "t.mp3"
    audio.write_text("a")
    db.save_call_summary("sid", "111", "222", str(transcript), "s", None)

    app = _setup_app("user")
    with app.test_request_context(
        "/v1/calls/1/delete", method="POST", data={"csrf_token": "tok"}
    ):
        login_user(DummyUser("user"))
        session["csrf_token"] = "tok"
        with pytest.raises(Forbidden):
            delete_call(1)

    assert transcript.exists()
    assert audio.exists()


def test_reprocess_call_triggers_task(monkeypatch, tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("SECRET_KEY", "x")
    db = migrate_sqlite(monkeypatch, tmp_path)
    db.create_user("admin", "pass", role="admin")
    tdir = tmp_path / "transcripts"
    tdir.mkdir()
    transcript = tdir / "t.txt"
    transcript.write_text("hi")
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    monkeypatch.setattr("server.dashboard_bp.DEFAULT_OUTPUT_DIR", audio_dir)
    audio_dir.joinpath("t.mp3").write_text("a")
    db.save_call_summary("sid", "111", "222", str(transcript), "s", None)

    called = []

    def fake_delay(cid):
        called.append(cid)

    monkeypatch.setattr(
        "server.dashboard_bp.reprocess_call_task",
        types.SimpleNamespace(delay=fake_delay),
    )

    app = _setup_app("admin")
    with app.test_request_context(
        "/v1/calls/1/reprocess", method="POST", data={"csrf_token": "tok"}
    ):
        login_user(DummyUser("admin"))
        session["csrf_token"] = "tok"
        resp = reprocess_call(1)

    assert resp.status_code == 302
    assert called == [1]
