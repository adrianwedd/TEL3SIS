from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import fakeredis

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools.calendar import create_event, list_events
from server.state_manager import StateManager


class DummyInsert:
    def __init__(self) -> None:
        self.body = None

    def execute(self) -> dict:
        return {"id": "evt"}


class DummyList:
    def __init__(self) -> None:
        self.kwargs: dict[str, Any] = {}

    def execute(self) -> dict:
        return {"items": [{"id": "evt"}]}


class DummyEvents:
    def insert(self, calendarId: str, body: dict) -> DummyInsert:  # noqa: ANN001
        self.body = body
        return DummyInsert()

    def list(self, **kwargs: Any) -> DummyList:
        dl = DummyList()
        dl.kwargs = kwargs
        return dl


class DummyService:
    def __init__(self) -> None:
        self._events = DummyEvents()

    def events(self) -> DummyEvents:
        return self._events


def _make_manager(monkeypatch: Any) -> StateManager:
    manager = StateManager(url="redis://localhost:6379/0")
    manager._redis = fakeredis.FakeRedis(decode_responses=True)
    manager.set_token("user", "tok", "rt", expires_at=9999999999)
    return manager


def _patch_build(monkeypatch: Any, service: DummyService) -> None:
    def fake_build(
        service_name: str, version: str, credentials: Any
    ) -> DummyService:  # noqa: ANN001
        assert service_name == "calendar"
        assert version == "v3"
        return service

    monkeypatch.setattr("tools.calendar.build", fake_build)


def test_create_and_list_events(monkeypatch: Any) -> None:
    manager = _make_manager(monkeypatch)
    service = DummyService()
    _patch_build(monkeypatch, service)

    start = datetime.utcnow()
    end = start + timedelta(hours=1)

    result = create_event(manager, "user", "Meeting", start, end)
    assert result["id"] == "evt"
    assert service._events.body["summary"] == "Meeting"

    events = list_events(manager, "user", start, end)
    assert events == [{"id": "evt"}]
