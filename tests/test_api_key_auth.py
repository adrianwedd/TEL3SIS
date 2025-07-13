import base64
import sys
from pathlib import Path
import pytest
from .db_utils import migrate_sqlite

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tests.utils.vocode_mocks import install as install_vocode

install_vocode()


class Dummy:
    def __init__(self, *args: object, **kwargs: object) -> None:
        pass


async def setup_app(monkeypatch, tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("EMBEDDING_MODEL_NAME", "dummy-model")
    monkeypatch.setattr("server.vector_db.SentenceTransformer", Dummy)
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())
    db_module = migrate_sqlite(monkeypatch, tmp_path)
    key = db_module.create_api_key("tester")
    from server.app import create_app  # noqa: E402
    from server.config import Config
    import httpx

    app = create_app(Config())
    transport = httpx.ASGITransport(app=app)
    client = httpx.AsyncClient(transport=transport, base_url="http://test")
    return client, key, db_module


@pytest.mark.asyncio
async def test_missing_key(monkeypatch, tmp_path):
    client, _, _ = await setup_app(monkeypatch, tmp_path)
    resp = await client.get("/v1/calls")
    await client.aclose()
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_invalid_key(monkeypatch, tmp_path):
    client, _, _ = await setup_app(monkeypatch, tmp_path)
    resp = await client.get("/v1/calls", headers={"X-API-Key": "bad"})
    await client.aclose()
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_valid_key(monkeypatch, tmp_path):
    client, key, db_module = await setup_app(monkeypatch, tmp_path)
    db_module.save_call_summary("abc", "111", "222", "/p", "s", None)
    monkeypatch.setenv("OAUTH_CLIENT_ID", "cid")
    monkeypatch.setenv("OAUTH_AUTH_URL", "https://auth.example/authorize")
    from urllib.parse import urlparse, parse_qs

    state = parse_qs(
        urlparse(
            (await client.get("/v1/login/oauth", headers={"X-API-Key": key})).headers[
                "Location"
            ]
        ).query
    )["state"][0]
    await client.get(
        f"/v1/oauth/callback?state={state}&user=admin", headers={"X-API-Key": key}
    )
    resp = await client.get("/v1/calls", headers={"X-API-Key": key})
    await client.aclose()
    assert resp.status_code == 200
