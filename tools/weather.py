from __future__ import annotations

import requests
from loguru import logger
from server.cache import redis_cache
from .base import Tool

__all__ = ["get_weather", "WeatherTool"]


@redis_cache(ttl=3600)
def get_weather(location: str) -> str:
    """Return a simple weather report for the given location."""
    url = f"https://wttr.in/{location}?format=j1"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        condition = data["current_condition"][0]
        desc = condition["weatherDesc"][0]["value"]
        temp_c = condition["temp_C"]
        return (
            f"The weather in {location} is {desc.lower()} with a temperature of "
            f"{temp_c}\N{DEGREE SIGN}C."
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to fetch weather for %s: %s", location, exc)
        return "Sorry, I'm unable to retrieve the weather right now."


class WeatherTool(Tool):
    """Tool wrapper for ``get_weather``."""

    name = "get_weather"
    description = "Get the current weather for a location."
    parameters = {
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City or region name"}
        },
        "required": ["location"],
    }

    def run(self, location: str) -> str:  # type: ignore[override]
        return get_weather(location)
