import base64
import sys
import types
from pathlib import Path
from .db_utils import migrate_sqlite

sys.path.append(str(Path(__file__).resolve().parents[1]))

import fakeredis
from fastapi.testclient import TestClient

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

from tests.utils.vocode_mocks import install as install_vocode  # noqa: E402

install_vocode()

import server.app as server_app  # noqa: E402
import server.state_manager as sm  # noqa: E402
import server.vector_db as vdb  # noqa: E402
from server.settings import Settings  # noqa: E402


class DummyModel:
    def __init__(self, *_: object, **__: object) -> None:
        pass

    def encode(self, texts: list[str]):
        import numpy as np

        return np.zeros((len(texts), 2))


class DummyClient:
    def __init__(self, *_: object, **__: object) -> None:
        pass

    def get_or_create_collection(self, *_: object, **__: object):
        return types.SimpleNamespace(
            add=lambda **__: None, query=lambda **__: {"documents": [[]]}
        )

    def heartbeat(self) -> int:
        return 1


def setup_app(monkeypatch, tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"0" * 16).decode())
    monkeypatch.setenv("EMBEDDING_MODEL_NAME", "dummy-model")
    monkeypatch.setenv("VECTOR_DB_PATH", str(tmp_path / "vectors"))

    monkeypatch.setattr(vdb, "SentenceTransformer", DummyModel)
    monkeypatch.setattr(vdb.chromadb, "PersistentClient", lambda *a, **k: DummyClient())
    monkeypatch.setattr(sm, "redis", types.SimpleNamespace(Redis=fakeredis.FakeRedis))

    db = migrate_sqlite(monkeypatch, tmp_path)
    key = db.create_api_key("tester")

    app = server_app.create_app(Settings())
    client = TestClient(app)
    return client, key


def test_health_endpoint(monkeypatch, tmp_path):
    client, key = setup_app(monkeypatch, tmp_path)
    resp = client.get("/v1/health", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"redis": "ok", "database": "ok", "chromadb": "ok"}
