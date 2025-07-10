import types
import sys
import os
import base64
from importlib import reload
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

# Provide dummy "vocode" modules so that server.app can be imported without the real dependency.
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

from server import database as db  # noqa: E402
from server.app import create_app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

os.environ.setdefault("SECRET_KEY", "x")
os.environ.setdefault("BASE_URL", "http://localhost")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "sid")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "token")
os.environ.setdefault("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())


def test_dashboard_oauth_flow(monkeypatch, tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())
    reload(db)
    db.init_db()
    db.create_user("admin", "pass", role="admin")
    transcript_dir = tmp_path / "transcripts"
    transcript_dir.mkdir()
    transcript_path = transcript_dir / "test.txt"
    transcript_path.write_text("hello world")
    db.save_call_summary("abc", "111", "222", str(transcript_path), "summary", "crit")
    key = db.create_api_key("tester")

    app = create_app()
    client = TestClient(app)

    resp = client.get("/v1/dashboard", headers={"X-API-Key": key})
    assert resp.status_code == 302
    assert "/v1/login/oauth" in resp.headers["Location"]

    monkeypatch.setenv("OAUTH_CLIENT_ID", "cid")
    monkeypatch.setenv("OAUTH_AUTH_URL", "https://auth.example/authorize")

    resp = client.get("/v1/login/oauth", headers={"X-API-Key": key})
    assert resp.status_code == 302
    assert resp.headers["Location"].startswith("https://auth.example/authorize")
    from urllib.parse import urlparse, parse_qs

    state = parse_qs(urlparse(resp.headers["Location"]).query)["state"][0]

    resp = client.get(
        f"/v1/oauth/callback?state={state}&user=admin", headers={"X-API-Key": key}
    )
    assert resp.status_code == 302

    resp = client.get("/v1/dashboard", headers={"X-API-Key": key})
    assert resp.status_code == 200

    resp = client.get("/v1/dashboard?q=111", headers={"X-API-Key": key})
    assert resp.status_code == 200
    assert b"111" in resp.content

    resp = client.get("/v1/dashboard/1", headers={"X-API-Key": key})
    assert resp.status_code == 200
    assert b"hello world" in resp.content


def test_oauth_callback_validation(monkeypatch) -> None:
    from server.app import create_app

    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())

    app = create_app()
    client = TestClient(app)
    key = db.create_api_key("tester")

    resp = client.get("/v1/oauth/callback", headers={"X-API-Key": key})
    assert resp.status_code == 400
    assert resp.json()["error"] == "invalid_request"


def test_dashboard_theme_toggle_template() -> None:
    """Ensure dashboard template includes theme toggle button."""
    from flask import Flask, render_template
    from server.dashboard_bp import bp as dashboard_bp

    app = Flask(__name__)
    app.register_blueprint(dashboard_bp)

    with app.test_request_context("/v1/dashboard", headers={"Cookie": "theme=dark"}):
        html = render_template("dashboard/list.html", calls=[], q="")

    assert '<button class="theme-toggle"' in html


def test_dashboard_prefix_search_with_formatted_number(monkeypatch, tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv(
        "TOKEN_ENCRYPTION_KEY",
        base64.b64encode(b"0" * 16).decode(),
    )
    reload(db)
    db.init_db()
    db.create_user("admin", "pass", role="admin")
    transcript_dir = tmp_path / "transcripts"
    transcript_dir.mkdir()
    transcript_path = transcript_dir / "t.txt"
    transcript_path.write_text("hi")
    db.save_call_summary(
        "sid1",
        "+12345678900",
        "999",
        str(transcript_path),
        "summary",
        "crit",
    )
    key = db.create_api_key("tester")

    app = create_app()
    client = TestClient(app)

    resp = client.get("/v1/dashboard", headers={"X-API-Key": key})
    assert resp.status_code == 302

    monkeypatch.setenv("OAUTH_CLIENT_ID", "cid")
    monkeypatch.setenv("OAUTH_AUTH_URL", "https://auth.example/authorize")
    from urllib.parse import urlparse, parse_qs

    state = parse_qs(
        urlparse(
            client.get("/v1/login/oauth", headers={"X-API-Key": key}).headers[
                "Location"
            ]
        ).query
    )["state"][0]

    client.get(
        f"/v1/oauth/callback?state={state}&user=admin", headers={"X-API-Key": key}
    )

    resp = client.get("/v1/dashboard?q=+1-234-567", headers={"X-API-Key": key})
    assert resp.status_code == 200
    assert b"+12345678900" in resp.content
