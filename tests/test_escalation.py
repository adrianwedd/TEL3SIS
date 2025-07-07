from __future__ import annotations

import base64
from typing import Any

import fakeredis
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from server.state_manager import StateManager
from server import escalation


def _make_manager(monkeypatch: Any) -> StateManager:
    key = AESGCM.generate_key(bit_length=128)
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(key).decode())
    manager = StateManager(url="redis://localhost:6379/0")
    manager._redis = fakeredis.FakeRedis(decode_responses=True)
    return manager


def test_contains_keyword() -> None:
    assert escalation.contains_keyword("This is an emergency situation")
    assert not escalation.contains_keyword("just chatting")


def test_check_and_flag(monkeypatch: Any) -> None:
    manager = _make_manager(monkeypatch)
    manager.create_session("call", {"foo": "bar"})
    flagged = escalation.check_and_flag(manager, "call", "I need a human operator")
    assert flagged
    assert manager.is_escalation_required("call")
