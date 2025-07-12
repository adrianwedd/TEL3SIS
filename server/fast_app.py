from __future__ import annotations

import os

from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ValidationError, HttpUrl
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from loguru import logger

from vocode.streaming.telephony.server.base import (
    TelephonyServer,
    TwilioInboundCallConfig,
)
from vocode.streaming.telephony.config_manager.in_memory_config_manager import (
    InMemoryConfigManager,
)
from vocode.streaming.models.telephony import TwilioConfig

from .database import (
    init_db,
    get_user_preference,
    set_user_preference,
    verify_api_key,
)
from .config import Config, ConfigError
from .handoff import dial_twiml
from .state_manager import StateManager
from .tasks import echo
from tools.notifications import send_sms
from tools.calendar import generate_auth_url, exchange_code
from agents.core_agent import build_core_agent, SafeAgentFactory
from .latency_logging import log_call
from .validation import validation_error_response


class InboundCallData(BaseModel):
    CallSid: str
    From: str
    To: str


class RecordingStatusData(BaseModel):
    CallSid: str
    RecordingSid: str
    RecordingUrl: HttpUrl


class OAuthStartData(BaseModel):
    user_id: str | None = None


class OAuthCallbackData(BaseModel):
    state: str
    user: str | None = None


def create_app() -> FastAPI:
    try:
        config = Config()
    except ConfigError as exc:
        raise RuntimeError(str(exc)) from exc

    app = FastAPI()

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

    @app.middleware("http")
    async def require_api_key(request: Request, call_next):
        if request.url.path.startswith("/v1/"):
            key = request.headers.get("X-API-Key")
            if not key or not verify_api_key(key):
                return Response("Unauthorized", status_code=401)
        return await call_next(request)

    @app.get("/v1/oauth/start")
    async def oauth_start(request: Request):
        try:
            data = OAuthStartData(**request.query_params)
        except ValidationError as exc:
            return validation_error_response(exc)
        url = generate_auth_url(state_manager, data.user_id or "")
        return RedirectResponse(url)

    @app.get("/v1/oauth/callback")
    async def oauth_callback(request: Request):
        try:
            data = OAuthCallbackData(**request.query_params)
        except ValidationError as exc:
            return validation_error_response(exc)
        exchange_code(state_manager, data.state, str(request.url))
        return "Authentication successful"

    @app.post("/v1/inbound_call")
    @log_call
    async def inbound_call(request: Request):
        try:
            form = await request.form()
            data = InboundCallData(**form)
        except ValidationError as exc:
            return validation_error_response(exc)

        call_sid = data.CallSid
        state_manager.create_session(
            call_sid,
            {"from": data.From, "to": data.To},
        )
        echo.delay(f"Call {call_sid} started")

        language = get_user_preference(data.From, "language")
        if not language:
            from tools.language import guess_language_from_number

            language = guess_language_from_number(data.From)
            set_user_preference(data.From, "language", language)
        if hasattr(state_manager, "update_session"):
            state_manager.update_session(call_sid, language=language)

        config_obj = build_core_agent(state_manager, call_sid, language=language)
        inbound_route = telephony_server.create_inbound_route(
            TwilioInboundCallConfig(
                url="/v1/inbound_call",
                agent_config=config_obj.agent,
                twilio_config=twilio_config,
            )
        )

        async def escalate():
            summary = state_manager.get_summary(call_sid) or ""
            send_sms(
                to_phone=os.environ.get("ESCALATION_PHONE_NUMBER", ""),
                from_phone=data.From,
                body=summary,
            )
            xml = dial_twiml(data.From)
            return Response(content=xml, media_type="text/xml")

        if state_manager.is_escalation_required(call_sid):
            return await escalate()

        response = await inbound_route(
            twilio_sid=data.CallSid,
            twilio_from=data.From,
            twilio_to=data.To,
        )

        if state_manager.is_escalation_required(call_sid):
            return await escalate()

        return Response(
            content=response.body,
            status_code=response.status_code,
            media_type=response.media_type,
        )

    @app.post("/v1/recording_status")
    async def recording_status(request: Request):
        try:
            form = await request.form()
            data = RecordingStatusData(**form)
        except ValidationError as exc:
            return validation_error_response(exc)

        logger.info(
            "Recording callback: call_sid=%s recording_sid=%s url=%s",
            data.CallSid,
            data.RecordingSid,
            data.RecordingUrl,
        )
        return Response(status_code=204)

    @app.get("/v1/metrics")
    async def metrics():
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )

    return app
