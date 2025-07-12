from __future__ import annotations

from importlib import reload
from pathlib import Path

from alembic import command
from alembic.config import Config as AlembicConfig


def migrate_sqlite(monkeypatch, tmp_path: Path):
    """Run Alembic migrations against a temporary SQLite database."""
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)

    cfg = AlembicConfig("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", db_url)
    import server.database as db

    try:
        command.upgrade(cfg, "head")
    except Exception:
        pass

    reload(db)
    db.init_db()
    return db
