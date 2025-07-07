from __future__ import annotations

import asyncio
import os
from flask import Flask, request, Response as FlaskResponse
from loguru import logger
from vocode.streaming.telephony.server.base import (
    TelephonyServer,
    TwilioInboundCallConfig,
)
from vocode.streaming.telephony.config_manager.in_memory_config_manager import (
    InMemoryConfigManager,
)
from vocode.streaming.models.telephony import TwilioConfig
from agents.core_agent import build_core_agent


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    base_url = os.environ.get("BASE_URL", "")
    twilio_config = TwilioConfig(
        account_sid=os.environ.get("TWILIO_ACCOUNT_SID", ""),
        auth_token=os.environ.get("TWILIO_AUTH_TOKEN", ""),
        record=True,
    )

    telephony_server = TelephonyServer(
        base_url=base_url,
        config_manager=InMemoryConfigManager(),
    )

    @app.post("/inbound_call")
    def inbound_call() -> FlaskResponse:  # type: ignore[return-type]
        """Handle POST requests from Twilio."""

        config = build_core_agent()
        inbound_route = telephony_server.create_inbound_route(
            TwilioInboundCallConfig(
                url="/inbound_call",
                agent_config=config.agent,
                twilio_config=twilio_config,
            )
        )

        async def handle() -> str:
            response = await inbound_route(
                twilio_sid=request.form.get("CallSid", ""),
                twilio_from=request.form.get("From", ""),
                twilio_to=request.form.get("To", ""),
            )
            return FlaskResponse(  # type: ignore[return-value]
                response.body,
                status=response.status_code,
                content_type=response.media_type,
            )

        return asyncio.run(handle())

    @app.post("/recording_status")
    def recording_status() -> str:
        """Receive recording status callbacks from Twilio."""

        recording_sid = request.form.get("RecordingSid", "")
        recording_url = request.form.get("RecordingUrl", "")
        call_sid = request.form.get("CallSid", "")
        logger.info(
            f"Recording callback: call_sid={call_sid} recording_sid={recording_sid} url={recording_url}"
        )
        return "", 204

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
