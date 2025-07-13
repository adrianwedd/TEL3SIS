from __future__ import annotations

from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .chat import manager as chat_manager
from .state_manager import StateManager
from .settings import Settings, ConfigError
from agents.core_agent import build_core_agent, SafeFunctionCallingAgent


def create_app(cfg: Optional[Settings] = None) -> FastAPI:
    """Return FastAPI app exposing a /chat/ws endpoint."""
    try:
        cfg = cfg or Settings()
        _ = cfg  # referenced to avoid unused variable warning
    except ConfigError as exc:
        raise RuntimeError(str(exc)) from exc

    app = FastAPI(title="TEL3SIS Chat API", version="1.0")

    state_manager = StateManager()

    @app.websocket("/chat/ws")
    async def chat_ws(websocket: WebSocket, session_id: str | None = None) -> None:
        """Bidirectional WebSocket chat with the core agent."""
        sid = session_id or str(uuid4())
        await chat_manager.connect(sid, websocket)
        state_manager.create_session(sid, {})

        config_obj = build_core_agent(state_manager, sid)
        agent = SafeFunctionCallingAgent(
            config_obj.agent, state_manager=state_manager, call_sid=sid
        )

        await websocket.send_json({"session_id": sid})
        try:
            while True:
                text = await websocket.receive_text()
                state_manager.append_history(sid, "user", text)
                async for resp in agent.generate_response(text, sid):
                    if hasattr(resp.message, "text"):
                        msg_text = getattr(resp.message, "text")
                        state_manager.append_history(sid, "assistant", msg_text)
                        await chat_manager.send_text(sid, msg_text)
        except WebSocketDisconnect:
            chat_manager.disconnect(sid)

    return app
