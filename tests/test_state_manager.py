from __future__ import annotations

import base64
import json
from typing import Any
import concurrent.futures
import pytest

import fakeredis
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from pathlib import Path

from server.state_manager import StateManager
from server.config import ConfigError


def _make_manager(monkeypatch: Any, tmp_path: Path) -> StateManager:
    key = AESGCM.generate_key(bit_length=128)
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(key).decode())
    monkeypatch.setenv("VECTOR_DB_PATH", str(tmp_path / "vectors"))
    monkeypatch.setenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    manager = StateManager(url="redis://localhost:6379/0")
    manager._redis = fakeredis.FakeRedis(decode_responses=True)
    return manager


def test_token_crud(monkeypatch, tmp_path):
    manager = _make_manager(monkeypatch, tmp_path)
    manager.set_token("user1", "at", "rt", expires_at=123)
    data = manager.get_token("user1")
    assert data == {"access_token": "at", "refresh_token": "rt", "expires_at": "123"}
    manager.delete_token("user1")
    assert manager.get_token("user1") is None


def test_oauth_state(monkeypatch, tmp_path):
    manager = _make_manager(monkeypatch, tmp_path)
    manager.set_oauth_state("abc", "user1", ttl=1)
    assert manager.pop_oauth_state("abc") == "user1"
    assert manager.pop_oauth_state("abc") is None


def test_history_and_summary(monkeypatch: Any, tmp_path: Path) -> None:
    manager = _make_manager(monkeypatch, tmp_path)
    manager.create_session("call", {"init": "1", "from": "+1"})
    manager.append_history("call", "user", "hi there")
    manager.append_history("call", "bot", "hello")
    history = manager.get_history("call")
    assert history[0]["text"] == "hi there"
    manager.set_summary("call", "greeting", from_number="+1")
    assert manager.get_summary("call") == "greeting"


def test_similar_summaries(monkeypatch: Any, tmp_path: Path) -> None:
    manager = _make_manager(monkeypatch, tmp_path)
    manager.set_summary(
        "c1", "User asked about the weather forecast", from_number="111"
    )
    manager.set_summary("c2", "Discussion on holiday plans", from_number="222")
    monkeypatch.setattr(
        manager._summary_db,
        "search",
        lambda *_, **__: ["User asked about the weather forecast"],
    )
    sims = manager.get_similar_summaries("weather", n_results=2)
    assert sims == ["User asked about the weather forecast"]


def test_create_session_loads_history(monkeypatch: Any, tmp_path: Path) -> None:
    manager = _make_manager(monkeypatch, tmp_path)
    manager.set_summary("c1", "Previous conversation", from_number="123")
    monkeypatch.setattr(
        manager._summary_db,
        "search",
        lambda *_, **__: ["Previous conversation"],
    )
    manager.create_session("new", {"from": "123"})
    sess = manager.get_session("new")
    sims = json.loads(sess.get("similar_summaries", "[]"))
    assert sims == ["Previous conversation"]


def test_missing_encryption_key(monkeypatch: Any, tmp_path: Path) -> None:
    monkeypatch.delenv("TOKEN_ENCRYPTION_KEY", raising=False)
    monkeypatch.setenv("VECTOR_DB_PATH", str(tmp_path / "vectors"))
    with pytest.raises(ConfigError):
        StateManager(url="redis://localhost:6379/0")


def test_invalid_encryption_key_length(monkeypatch: Any, tmp_path: Path) -> None:
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"short").decode())
    monkeypatch.setenv("VECTOR_DB_PATH", str(tmp_path / "vectors"))
    with pytest.raises(ConfigError):
        StateManager(url="redis://localhost:6379/0")


def test_concurrent_history_updates(monkeypatch: Any, tmp_path: Path) -> None:
    manager = _make_manager(monkeypatch, tmp_path)
    manager.create_session("call", {})

    def add(i: int) -> None:
        manager.append_history("call", "user", f"msg{i}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as exc:
        exc.map(add, range(5))

    history = manager.get_history("call")
    assert len(history) == 5
    texts = {h["text"] for h in history}
    assert texts == {f"msg{i}" for i in range(5)}
