"""Abstract base classes and registry for callable tools."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class Tool(ABC):
    """Abstract base class for callable tools."""

    name: str
    description: str
    parameters: Dict[str, Any]

    @abstractmethod
    def run(self, **kwargs: Any) -> Any:
        """Execute the tool and return a result."""

    def schema(self) -> Dict[str, Any]:
        """Return OpenAI function schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ToolRegistry:
    """Registry mapping tool names and intents to tool instances."""

    def __init__(self) -> None:
        self.tools: Dict[str, Tool] = {}
        self.intent_map: Dict[str, str] = {}

    def register(self, tool: Tool, intent: str | None = None) -> None:
        self.tools[tool.name] = tool
        if intent:
            self.intent_map[intent] = tool.name

    def by_name(self, name: str) -> Tool | None:
        return self.tools.get(name)

    def by_intent(self, intent: str) -> Tool | None:
        name = self.intent_map.get(intent)
        return self.tools.get(name) if name else None

    def schemas(self) -> List[Dict[str, Any]]:
        return [tool.schema() for tool in self.tools.values()]


registry = ToolRegistry()
