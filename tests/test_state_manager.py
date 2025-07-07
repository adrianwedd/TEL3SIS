from __future__ import annotations

import base64
from typing import Any

import fakeredis
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from server.state_manager import StateManager


def _make_manager(monkeypatch: Any) -> StateManager:
    key = AESGCM.generate_key(bit_length=128)
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(key).decode())
    manager = StateManager(url="redis://localhost:6379/0")
    manager._redis = fakeredis.FakeRedis(decode_responses=True)
    return manager


def test_token_crud(monkeypatch):
    manager = _make_manager(monkeypatch)
    manager.set_token("user1", "at", "rt", expires_at=123)
    data = manager.get_token("user1")
    assert data == {"access_token": "at", "refresh_token": "rt", "expires_at": "123"}
    manager.delete_token("user1")
    assert manager.get_token("user1") is None


def test_oauth_state(monkeypatch):
    manager = _make_manager(monkeypatch)
    manager.set_oauth_state("abc", "user1", ttl=1)
    assert manager.pop_oauth_state("abc") == "user1"
    assert manager.pop_oauth_state("abc") is None
