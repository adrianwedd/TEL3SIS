import types
import os
import base64
import fakeredis
from .db_utils import migrate_sqlite

from tests.utils.vocode_mocks import install as install_vocode

install_vocode()

os.environ.setdefault("SECRET_KEY", "x")
os.environ.setdefault("BASE_URL", "http://localhost")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "sid")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "token")
os.environ.setdefault("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())

import server.state_manager as sm  # noqa: E402


def test_rate_limits(monkeypatch, tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("CALL_RATE_LIMIT", "1/minute")
    monkeypatch.setenv("API_RATE_LIMIT", "1/minute")
    monkeypatch.setenv("RATE_LIMIT_REDIS_URL", "memory://")
    db = migrate_sqlite(monkeypatch, tmp_path)
    key = db.create_api_key("tester")

    monkeypatch.setattr(sm, "redis", types.SimpleNamespace(Redis=fakeredis.FakeRedis))

    from server.app import create_app  # noqa: E402
    from server.config import Config
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

    app = create_app(Config())
    client = TestClient(app)
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
