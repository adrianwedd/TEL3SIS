import base64
import types
from urllib.parse import parse_qs, urlparse

import fakeredis
from fastapi.testclient import TestClient

from tests.db_utils import migrate_sqlite
from tests.utils.vocode_mocks import install as install_vocode

install_vocode()

import server.app as server_app  # noqa: E402
import server.state_manager as sm  # noqa: E402
from server.app import create_app  # noqa: E402
from server.config import Config  # noqa: E402


def _setup(monkeypatch, tmp_path):
    db = migrate_sqlite(monkeypatch, tmp_path)
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())
    monkeypatch.setattr(sm, "redis", types.SimpleNamespace(Redis=fakeredis.FakeRedis))
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "cid")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret")
    monkeypatch.setenv("OAUTH_AUTH_URL", "https://auth.example/authorize")
    key = db.create_api_key("tester")
    app = create_app(Config())
    client = TestClient(app)
    return client, key


def test_oauth_consent_page(monkeypatch, tmp_path):
    client, key = _setup(monkeypatch, tmp_path)
    resp = client.get("/v1/oauth/consent?user_id=admin", headers={"X-API-Key": key})
    assert resp.status_code == 200
    assert "https://www.googleapis.com/auth/calendar" in resp.text


def test_oauth_callback_stores_token(monkeypatch, tmp_path):
    tokens = {}

    class DummyStateManager(sm.StateManager):
        def __init__(self, *args, **kwargs):
            super().__init__(url="redis://localhost:6379/0")
            self._redis = fakeredis.FakeRedis(decode_responses=True)
            tokens["mgr"] = self

    monkeypatch.setattr(server_app, "StateManager", DummyStateManager)
    client, key = _setup(monkeypatch, tmp_path)

    resp = client.get("/v1/login/oauth", headers={"X-API-Key": key})
    state = parse_qs(urlparse(resp.headers["Location"]).query)["state"][0]

    def fake_exchange(manager, state, url):
        manager.set_token("admin", "tok", "rt", 1)

    monkeypatch.setattr(server_app, "exchange_code", fake_exchange)

    resp = client.get(
        f"/v1/oauth/callback?state={state}&user=admin", headers={"X-API-Key": key}
    )
    assert resp.status_code == 302
    assert tokens["mgr"].get_token("admin")["access_token"] == "tok"
