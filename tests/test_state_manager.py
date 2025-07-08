from __future__ import annotations

import base64
from typing import Any

import fakeredis
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from pathlib import Path

from server.state_manager import StateManager


def _make_manager(monkeypatch: Any, tmp_path: Path) -> StateManager:
    key = AESGCM.generate_key(bit_length=128)
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(key).decode())
    monkeypatch.setenv("VECTOR_DB_PATH", str(tmp_path / "vectors"))
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
    manager.create_session("call", {"init": "1"})
    manager.append_history("call", "user", "hi there")
    manager.append_history("call", "bot", "hello")
    history = manager.get_history("call")
    assert history[0]["text"] == "hi there"
    manager.set_summary("call", "greeting")
    assert manager.get_summary("call") == "greeting"


def test_similar_summaries(monkeypatch: Any, tmp_path: Path) -> None:
    manager = _make_manager(monkeypatch, tmp_path)
    manager.set_summary("c1", "User asked about the weather forecast")
    manager.set_summary("c2", "Discussion on holiday plans")
    sims = manager.get_similar_summaries("weather", n_results=2)
    assert "User asked about the weather forecast" in sims
