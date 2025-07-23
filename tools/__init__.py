"""Registry of built-in tools and selection helpers."""

from __future__ import annotations

from agents.calendar_agent import CalendarAgent

from .base import registry, Tool
from .weather import WeatherTool, get_weather
from .calendar import CreateEventTool, ListEventsTool
from .translation import TranslateTool, translate_text
from .browser import BrowserTool, browse_url
from .sentiment import analyze_sentiment


# Register default tools
registry.register(WeatherTool())
registry.register(CreateEventTool(), intent="create_event")
registry.register(ListEventsTool(), intent="check_availability")
registry.register(TranslateTool())
registry.register(BrowserTool())

_calendar_agent = CalendarAgent()


def get_tool_for_intent(intent: str) -> Tool | None:
    """Return tool mapped to intent if available."""
    return registry.by_intent(intent)


def select_tool(text: str) -> Tool | None:
    """Detect intent from ``text`` and return the corresponding tool."""
    intent = _calendar_agent.detect_intent(text)
    return get_tool_for_intent(intent)


__all__ = [
    "registry",
    "get_tool_for_intent",
    "select_tool",
    "get_weather",
    "WeatherTool",
    "CreateEventTool",
    "ListEventsTool",
    "TranslateTool",
    "BrowserTool",
    "browse_url",
    "analyze_sentiment",
    "translate_text",
]
