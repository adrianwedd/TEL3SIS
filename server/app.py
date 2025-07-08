from __future__ import annotations

import asyncio
import os
from flask import Flask, request, Response as FlaskResponse, redirect, jsonify
from pydantic import BaseModel, HttpUrl, ValidationError
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


class InboundCallData(BaseModel):
    CallSid: str
    From: str
    To: str


class RecordingStatusData(BaseModel):
    CallSid: str
    RecordingSid: str
    RecordingUrl: HttpUrl


def _validation_error_response(exc: ValidationError) -> FlaskResponse:
    resp = jsonify({"error": "invalid_request", "details": exc.errors()})
    resp.status_code = 400
    return resp  # type: ignore[return-value]


def create_app() -> Flask:
    """Create and configure the Flask application."""
    try:
        config = Config()
    except ConfigError as exc:
        raise RuntimeError(str(exc)) from exc

    app = Flask(__name__)
    app.secret_key = config.secret_key
    app.register_blueprint(auth_bp, url_prefix="/v1")
    app.register_blueprint(calls_bp, url_prefix="/v1")
    app.register_blueprint(dashboard_bp, url_prefix="/v1")
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

    @app.get("/v1/oauth/start")
    def oauth_start() -> str:
        """Initiate Google OAuth flow and redirect user."""
        user_id = request.args.get("user_id", "")
        url = generate_auth_url(state_manager, user_id)
        return redirect(url)

    @app.get("/v1/oauth/callback")
    def oauth_callback() -> str:
        """Handle OAuth callback and store credentials."""
        state = request.args.get("state", "")
        exchange_code(state_manager, state, request.url)
        return "Authentication successful"

    @app.post("/v1/inbound_call")
    def inbound_call() -> FlaskResponse:  # type: ignore[return-type]
        """Handle POST requests from Twilio."""

        try:
            data = InboundCallData(**request.form)  # type: ignore[arg-type]
        except ValidationError as exc:
            return _validation_error_response(exc)

        call_sid = data.CallSid
        state_manager.create_session(
            call_sid,
            {
                "from": data.From,
                "to": data.To,
            },
        )
        echo.delay(f"Call {call_sid} started")

        config = build_core_agent(state_manager, call_sid)
        inbound_route = telephony_server.create_inbound_route(
            TwilioInboundCallConfig(
                url="/v1/inbound_call",
                agent_config=config.agent,
                twilio_config=twilio_config,
            )
        )

        async def handle() -> FlaskResponse:
            def escalate() -> FlaskResponse:
                summary = state_manager.get_summary(call_sid) or ""
                send_sms(
                    to_phone=os.environ.get("ESCALATION_PHONE_NUMBER", ""),
                    from_phone=data.From,
                    body=summary,
                )
                xml = dial_twiml(data.From)
                return FlaskResponse(xml, content_type="text/xml")

            if state_manager.is_escalation_required(call_sid):
                return escalate()

            response = await inbound_route(
                twilio_sid=data.CallSid,
                twilio_from=data.From,
                twilio_to=data.To,
            )

            if state_manager.is_escalation_required(call_sid):
                return escalate()

            return FlaskResponse(  # type: ignore[return-value]
                response.body,
                status=response.status_code,
                content_type=response.media_type,
            )

        return asyncio.run(handle())

    @app.post("/v1/recording_status")
    def recording_status() -> str:
        """Receive recording status callbacks from Twilio."""

        try:
            data = RecordingStatusData(**request.form)  # type: ignore[arg-type]
        except ValidationError as exc:
            return _validation_error_response(exc)

        logger.info(
            "Recording callback: call_sid=%s recording_sid=%s url=%s",
            data.CallSid,
            data.RecordingSid,
            data.RecordingUrl,
        )
        return "", 204

    @app.get("/v1/metrics")
    def metrics() -> FlaskResponse:
        """Expose Prometheus metrics."""
        return FlaskResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
