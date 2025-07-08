from __future__ import annotations

import asyncio
import os
from flask import Flask, request, Response as FlaskResponse, redirect
from flask_login import LoginManager
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from loguru import logger
from vocode.streaming.telephony.server.base import (
    TelephonyServer,
    TwilioInboundCallConfig,
)
from .handoff import dial_twiml
from tools.notifications import send_sms
from .calls_bp import bp as calls_bp
from .dashboard_bp import bp as dashboard_bp
from vocode.streaming.telephony.config_manager.in_memory_config_manager import (
    InMemoryConfigManager,
)
from vocode.streaming.models.telephony import TwilioConfig
from agents.core_agent import build_core_agent, SafeAgentFactory
from .state_manager import StateManager
from .tasks import echo
from .database import init_db, get_user
from .auth_bp import bp as auth_bp
from tools.calendar import generate_auth_url, exchange_code
from .config import Config, ConfigError


def create_app() -> Flask:
    """Create and configure the Flask application."""
    try:
        config = Config()
    except ConfigError as exc:
        raise RuntimeError(str(exc)) from exc

    app = Flask(__name__)
    app.secret_key = config.secret_key
    app.register_blueprint(auth_bp)
    app.register_blueprint(calls_bp)
    app.register_blueprint(dashboard_bp)
    login_manager = LoginManager()
    login_manager.login_view = "auth.login_form"

    @login_manager.user_loader
    def load_user(user_id: str):
        return get_user(int(user_id))

    login_manager.init_app(app)
    init_db()

    base_url = config.base_url
    twilio_config = TwilioConfig(
        account_sid=config.twilio_account_sid,
        auth_token=config.twilio_auth_token,
        record=True,
    )

    telephony_server = TelephonyServer(
        base_url=base_url,
        config_manager=InMemoryConfigManager(),
        agent_factory=SafeAgentFactory(),
    )
    try:
        state_manager = StateManager()
    except ConfigError as exc:
        raise RuntimeError(str(exc)) from exc

    @app.get("/oauth/start")
    def oauth_start() -> str:
        """Initiate Google OAuth flow and redirect user."""
        user_id = request.args.get("user_id", "")
        url = generate_auth_url(state_manager, user_id)
        return redirect(url)

    @app.get("/oauth/callback")
    def oauth_callback() -> str:
        """Handle OAuth callback and store credentials."""
        state = request.args.get("state", "")
        exchange_code(state_manager, state, request.url)
        return "Authentication successful"

    @app.post("/inbound_call")
    def inbound_call() -> FlaskResponse:  # type: ignore[return-type]
        """Handle POST requests from Twilio."""

        call_sid = request.form.get("CallSid", "")
        state_manager.create_session(
            call_sid,
            {
                "from": request.form.get("From", ""),
                "to": request.form.get("To", ""),
            },
        )
        echo.delay(f"Call {call_sid} started")

        config = build_core_agent(state_manager, call_sid)
        inbound_route = telephony_server.create_inbound_route(
            TwilioInboundCallConfig(
                url="/inbound_call",
                agent_config=config.agent,
                twilio_config=twilio_config,
            )
        )

        async def handle() -> FlaskResponse:
            def escalate() -> FlaskResponse:
                summary = state_manager.get_summary(call_sid) or ""
                send_sms(
                    to_phone=os.environ.get("ESCALATION_PHONE_NUMBER", ""),
                    from_phone=request.form.get("From", ""),
                    body=summary,
                )
                xml = dial_twiml(request.form.get("From", ""))
                return FlaskResponse(xml, content_type="text/xml")

            if state_manager.is_escalation_required(call_sid):
                return escalate()

            response = await inbound_route(
                twilio_sid=request.form.get("CallSid", ""),
                twilio_from=request.form.get("From", ""),
                twilio_to=request.form.get("To", ""),
            )

            if state_manager.is_escalation_required(call_sid):
                return escalate()

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

    @app.get("/metrics")
    def metrics() -> FlaskResponse:
        """Expose Prometheus metrics."""
        return FlaskResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
