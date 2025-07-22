"""WebSocket connection manager for chat sessions."""
from __future__ import annotations

from typing import Any, Dict
from uuid import uuid4

from fastapi import WebSocket


class ConnectionManager:
    """Track active WebSocket connections by session id."""

    def __init__(self) -> None:
        self.active: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        """Accept connection and register it."""
        await websocket.accept()
        self.active[session_id] = websocket

    def disconnect(self, session_id: str) -> None:
        """Remove a WebSocket connection."""
        self.active.pop(session_id, None)

    async def send_text(self, session_id: str, text: str) -> None:
        """Send ``text`` to the client for ``session_id`` if connected."""
        websocket = self.active.get(session_id)
        if websocket:
            await websocket.send_text(text)

    async def broadcast_json(self, data: Any) -> None:
        """Send ``data`` as JSON to all connected clients."""
        for websocket in list(self.active.values()):
            try:
                await websocket.send_json(data)
            except Exception:
                pass


manager = ConnectionManager()

__all__ = ["manager", "ConnectionManager", "uuid4"]
