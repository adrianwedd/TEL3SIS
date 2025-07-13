import base64
from urllib.parse import urlparse, parse_qs

from tests.db_utils import migrate_sqlite
from tests.utils.vocode_mocks import install as install_vocode

install_vocode()

from server.app import create_app  # noqa: E402
from server.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
import server.state_manager as sm  # noqa: E402
import fakeredis  # noqa: E402
import types  # noqa: E402


def setup_app(monkeypatch, tmp_path):
    db = migrate_sqlite(monkeypatch, tmp_path)
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())
    monkeypatch.setattr(sm, "redis", types.SimpleNamespace(Redis=fakeredis.FakeRedis))
    monkeypatch.setenv("OAUTH_CLIENT_ID", "cid")
    monkeypatch.setenv("OAUTH_AUTH_URL", "https://auth.example/authorize")
    key = db.create_api_key("tester")
    app = create_app(Config())
    client = TestClient(app)
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
    return client, key, db


def test_conversation_log(monkeypatch, tmp_path):
    client, key, db = setup_app(monkeypatch, tmp_path)
    t = tmp_path / "t.txt"
    t.write_text("hello")
    db.save_call_summary("sid1", "111", "222", str(t), "sum", None)
    with db.get_session() as session:
        call_id = session.query(db.Call).first().id
    resp = client.get(f"/v1/admin/conversations/{call_id}", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert data["transcript"] == "hello"


def test_agent_status(monkeypatch, tmp_path):
    client, key, _ = setup_app(monkeypatch, tmp_path)
    manager = sm.StateManager(url="redis://localhost:6379/0")
    manager._redis = fakeredis.FakeRedis(decode_responses=True)
    manager.create_session("sid", {"from": "1"})
    resp = client.get("/v1/admin/agent_status", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert data["active_sessions"] >= 1
