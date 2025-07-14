from __future__ import annotations

from importlib import reload
import os
import sys
from pathlib import Path

import pytest
from celery.contrib.testing.worker import start_worker
from tests.utils.vocode_mocks import install as install_vocode
import types

install_vocode()

# Stub chromadb globally to avoid heavy dependency
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
sys.modules.setdefault("chromadb", chroma)
sys.modules.setdefault("chromadb.api", types.ModuleType("chromadb.api"))
sys.modules.setdefault(
    "chromadb.api.types",
    types.SimpleNamespace(EmbeddingFunction=object, Embeddings=list),
)

os.environ.setdefault("SECRET_KEY", "x")
os.environ.setdefault("BASE_URL", "http://localhost")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "sid")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "token")
os.environ.setdefault("SENDGRID_API_KEY", "sg")
os.environ.setdefault("SENDGRID_FROM_EMAIL", "from@test")
os.environ.setdefault("NOTIFY_EMAIL", "notify@test")
os.environ.setdefault("USE_FAKE_SERVICES", "true")


@pytest.fixture
def celery_setup(monkeypatch, tmp_path):
    """Configure Celery and database for tests."""
    monkeypatch.setenv("CELERY_BROKER_URL", "memory://")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "cache+memory://")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    vector_dir = tmp_path / "vectors"
    monkeypatch.setenv("VECTOR_DB_PATH", str(vector_dir))
    vector_dir.mkdir()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    import server.celery_app as celery_app
    import server.tasks as tasks
    from .db_utils import migrate_sqlite

    db = migrate_sqlite(monkeypatch, tmp_path)

    reload(celery_app)
    celery_app.celery_app.conf.task_default_queue = "default"
    reload(tasks)
    return celery_app.celery_app, tasks, db


@pytest.fixture
def celery_worker(celery_setup):
    app, tasks, db = celery_setup
    with start_worker(app, queues=["default"], perform_ping_check=False):
        yield tasks, db
