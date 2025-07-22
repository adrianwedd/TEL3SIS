from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import inspect

from .db_utils import migrate_sqlite


def test_tables_exist(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    db = migrate_sqlite(monkeypatch, tmp_path)
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    assert "calls" in tables
    assert "user_preferences" in tables
    columns = [c["name"] for c in inspector.get_columns("calls")]
    assert "self_critique" in columns
    assert "sentiment" in columns


def test_save_call_summary(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    db = migrate_sqlite(monkeypatch, tmp_path)
    db.save_call_summary("abc", "111", "222", "/path", "summary", "crit", 0.5)
    with db.get_session() as session:
        result = session.query(db.Call).filter_by(call_sid="abc").one()
        assert result.summary == "summary"
        assert result.self_critique == "crit"
        assert result.sentiment == 0.5


def test_create_and_delete_user(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    db = migrate_sqlite(monkeypatch, tmp_path)
    db.create_user("alice", "pw")
    with db.get_session() as session:
        assert session.query(db.User).filter_by(username="alice").count() == 1
    assert db.delete_user("alice") is True
    with db.get_session() as session:
        assert session.query(db.User).filter_by(username="alice").count() == 0
    assert db.delete_user("alice") is False


def test_list_and_update_user(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    db = migrate_sqlite(monkeypatch, tmp_path)
    db.create_user("alice", "pw", role="user")
    db.create_user("bob", "pw", role="admin")

    users = db.list_users()
    assert [u.username for u in users] == ["alice", "bob"]

    assert db.update_user("alice", password="new", role="admin") is True
    updated = [u for u in db.list_users() if u.username == "alice"][0]
    assert updated.role == "admin"
