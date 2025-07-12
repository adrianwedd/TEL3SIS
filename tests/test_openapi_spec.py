import base64
import sys
from pathlib import Path
import httpx
import pytest
from .db_utils import migrate_sqlite

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tests.utils.vocode_mocks import install as install_vocode

install_vocode()

from server.app import create_app  # noqa: E402
from server.config import Config  # noqa: E402


def setup_client(monkeypatch, tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())
    migrate_sqlite(monkeypatch, tmp_path)
    app = create_app(Config())
    transport = httpx.ASGITransport(app=app)
    client = httpx.AsyncClient(transport=transport, base_url="http://test")
    return client


@pytest.mark.asyncio
async def test_openapi_spec(monkeypatch, tmp_path):
    client = setup_client(monkeypatch, tmp_path)
    resp = await client.get("/openapi.json")
    await client.aclose()
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
