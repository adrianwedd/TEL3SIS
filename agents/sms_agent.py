from __future__ import annotations

from typing import List

from agents.core_agent import SafeFunctionCallingAgent, build_core_agent
from server.state_manager import StateManager


class SMSAgent:
    """Simple agent wrapper for processing SMS conversations."""

    def __init__(self, state_manager: StateManager, session_id: str) -> None:
        self._state_manager = state_manager
        self._session_id = session_id
        config = build_core_agent(state_manager, session_id).agent
        self._agent = SafeFunctionCallingAgent(
            config, state_manager=state_manager, call_sid=session_id
        )

    async def handle_message(self, text: str) -> str:
        """Return agent response text for ``text``."""
        parts: List[str] = []
        async for chunk in self._agent.generate_response(text, self._session_id):
            if hasattr(chunk.message, "text"):
                parts.append(getattr(chunk.message, "text"))
        return "".join(parts).strip()
