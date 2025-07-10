from __future__ import annotations

import requests

from tools.weather import get_weather


class DummyResponse:
    def __init__(self, data: dict, status_code: int = 200) -> None:
        self._data = data
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError()

    def json(self) -> dict:
        return self._data


def test_get_weather(monkeypatch):
    data = {
        "current_condition": [{"temp_C": "20", "weatherDesc": [{"value": "Sunny"}]}]
    }

    def fake_get(url: str, timeout: int = 5) -> DummyResponse:  # noqa: ARG001
        return DummyResponse(data)

    monkeypatch.setattr(requests, "get", fake_get)
    result = get_weather("London")
    assert "20" in result
    assert "sunny" in result.lower()


def test_get_weather_failure(monkeypatch):
    def fake_get(url: str, timeout: int = 5):  # noqa: ARG001
        raise requests.RequestException("boom")

    monkeypatch.setattr(requests, "get", fake_get)
    result = get_weather("Paris")
    assert "unable to" in result.lower()
