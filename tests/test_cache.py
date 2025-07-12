from __future__ import annotations

import fakeredis

from tools import weather
from server import self_reflection
from server import cache


class DummyClient:
    def __init__(self) -> None:
        self.calls = 0
        self.chat = type(
            "Chat", (), {"completions": type("C", (), {"create": self._create})}
        )()

    def _create(self, *args: object, **kwargs: object):
        self.calls += 1
        return {"choices": [{"message": {"content": "ok"}}]}


def test_weather_cached(monkeypatch):
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(cache, "_redis", fake)

    called = {}

    def fake_get(url: str, timeout: int = 5):  # noqa: ARG001
        called["n"] = called.get("n", 0) + 1

        class Resp:
            status_code = 200

            def raise_for_status(self):
                pass

            def json(self):
                return {
                    "current_condition": [
                        {"temp_C": "10", "weatherDesc": [{"value": "Sunny"}]}
                    ]
                }

        return Resp()

    monkeypatch.setattr(weather.requests, "get", fake_get)

    r1 = weather.get_weather("Paris")
    r2 = weather.get_weather("Paris")
    assert r1 == r2
    assert called["n"] == 1


def test_self_reflection_cached(monkeypatch):
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(cache, "_redis", fake)

    client = DummyClient()
    r1 = self_reflection.generate_self_critique("hi", client=client)
    r2 = self_reflection.generate_self_critique("hi", client=client)
    assert r1 == r2
    assert client.calls == 1
