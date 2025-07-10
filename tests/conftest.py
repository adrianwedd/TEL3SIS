from __future__ import annotations

from importlib import reload
import os
import sys
from pathlib import Path

import pytest
from celery.contrib.testing.worker import start_worker

os.environ.setdefault("SECRET_KEY", "x")
os.environ.setdefault("BASE_URL", "http://localhost")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "sid")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "token")
os.environ.setdefault("SENDGRID_API_KEY", "sg")
os.environ.setdefault("SENDGRID_FROM_EMAIL", "from@test")
os.environ.setdefault("NOTIFY_EMAIL", "notify@test")


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
