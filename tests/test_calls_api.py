import types
import sys
import os
import base64
from fastapi.testclient import TestClient
from .db_utils import migrate_sqlite
from tests.utils.vocode_mocks import install as install_vocode

install_vocode()


# Stub chromadb to avoid importing heavy dependency
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


os.environ.setdefault("SECRET_KEY", "x")
os.environ.setdefault("BASE_URL", "http://localhost")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "sid")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "token")
os.environ.setdefault("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())

from server.app import create_app  # noqa: E402
from server.settings import Settings  # noqa: E402


def test_list_calls(monkeypatch, tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())
    db = migrate_sqlite(monkeypatch, tmp_path)
    db.save_call_summary("abc", "111", "222", "/path", "summary", "crit")
    key = db.create_api_key("tester")

    app = create_app(Settings())
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
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["call_sid"] == "abc"


def test_list_calls_filters_and_pagination(monkeypatch, tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())
    db = migrate_sqlite(monkeypatch, tmp_path)
    from datetime import datetime, timedelta, UTC

    early = datetime.now(UTC) - timedelta(days=2)
    with db.get_session() as session:
        session.add(
            db.Call(
                call_sid="a",
                from_number="111",
                to_number="222",
                transcript_path="/p",
                summary="s",
                self_critique=None,
                created_at=early,
            )
        )
        session.commit()
    db.save_call_summary("b", "333", "222", "/p", "s", "crit")
    db.save_call_summary("c", "333", "555", "/p", "s", None)
    key = db.create_api_key("tester")

    app = create_app(Settings())
    client = TestClient(app)

    start = (early + timedelta(days=1)).isoformat()
    resp = client.get(
        "/v1/calls",
        params={"start": start, "page_size": 1},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 1

    resp = client.get("/v1/calls?phone=555", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["from_number"] == "333"
