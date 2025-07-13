from __future__ import annotations

from typing import List, Optional
import re

from server.database import set_user_preference

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

    def _command_response(self, text: str) -> Optional[str]:
        """Return response text if ``text`` is a command."""
        m = re.match(r"\s*(?:lang|language)[:\s]+([a-zA-Z-]+)", text)
        if m:
            code = m.group(1)
            session = self._state_manager.get_session(self._session_id)
            from_number = session.get("from")
            if from_number:
                set_user_preference(from_number, "language", code)
            return f"Language set to {code}"
        if text.strip().lower() == "help":
            return "Commands: language <code>"
        return None

    async def handle_message(self, text: str) -> str:
        """Return agent response text for ``text``."""
        cmd = self._command_response(text)
        if cmd is not None:
            return cmd
        parts: List[str] = []
        async for chunk in self._agent.generate_response(text, self._session_id):
            if hasattr(chunk.message, "text"):
                parts.append(getattr(chunk.message, "text"))
        return "".join(parts).strip()
