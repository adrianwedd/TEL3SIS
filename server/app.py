from __future__ import annotations

import os
import re
import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from apispec import APISpec
from pydantic import BaseModel, Field, HttpUrl, ValidationError
from datetime import datetime
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from logging_config import logger
from starlette.middleware.sessions import SessionMiddleware
from fastapi.openapi.utils import get_openapi

from vocode.streaming.telephony.server.base import (
    TelephonyServer,
    TwilioInboundCallConfig,
)
from vocode.streaming.telephony.config_manager.in_memory_config_manager import (
    InMemoryConfigManager,
)
from vocode.streaming.models.telephony import TwilioConfig

from .database import (
    Call,
    get_session,
    get_user_preference,
    init_db,
    set_user_preference,
    verify_api_key,
)
from .config import Config, ConfigError
from .handoff import dial_twiml
from .state_manager import StateManager
from .tasks import echo
from tools.notifications import send_sms
from tools.calendar import exchange_code, generate_auth_url
from agents.core_agent import build_core_agent, SafeAgentFactory
from .latency_logging import log_call


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


class CallInfo(BaseModel):
    id: int
    call_sid: str
    from_number: str
    to_number: str
    transcript_path: str
    summary: str | None
    self_critique: str | None
    created_at: datetime


class ListCallsQuery(BaseModel):
    """Parameters for filtering and paginating call history."""

    start: datetime | None = None
    end: datetime | None = None
    phone: str | None = None
    error: bool | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort: str = "-timestamp"


class _SimpleLimiter:
    def __init__(self, limit: int, interval: float) -> None:
        self.limit = limit
        self.interval = interval
        self.calls: dict[str, list[float]] = {}

    def allow(self, key: str) -> bool:
        from time import monotonic

        now = monotonic()
        items = [t for t in self.calls.get(key, []) if now - t < self.interval]
        if len(items) >= self.limit:
            self.calls[key] = items
            return False
        items.append(now)
        self.calls[key] = items
        return True


def _parse_rate(value: str) -> tuple[int, float]:
    try:
        limit, per = value.split("/")
        limit = int(limit)
        interval = 60 if per.endswith("minute") else 1
    except Exception:
        return 1000, 60
    return limit, interval


def _json_validation_error(exc: ValidationError) -> JSONResponse:
    return JSONResponse(
        {"error": "invalid_request", "details": exc.errors()}, status_code=400
    )


def create_app() -> FastAPI:
    try:
        config = Config()
    except ConfigError as exc:
        raise RuntimeError(str(exc)) from exc

    app = FastAPI(
        title="TEL3SIS API",
        version="1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )
    app.state.spec = APISpec(
        title=app.title,
        version=app.version,
        openapi_version="3.0.3",
    )

    def custom_openapi() -> dict:
        if not hasattr(app.state, "spec_dict"):
            schema = get_openapi(
                title=app.title,
                version=app.version,
                routes=app.routes,
            )
            app.state.spec_dict = schema
        return app.state.spec_dict

    app.openapi = custom_openapi
    app.add_middleware(SessionMiddleware, secret_key=config.secret_key)

    init_db()

    call_limit, call_interval = _parse_rate(os.getenv("CALL_RATE_LIMIT", "3/minute"))
    api_limit, api_interval = _parse_rate(os.getenv("API_RATE_LIMIT", "60/minute"))
    call_limiter = _SimpleLimiter(call_limit, call_interval)
    api_limiter = _SimpleLimiter(api_limit, api_interval)

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
    async def verify_key(request: Request, call_next):
        if request.url.path.startswith("/v1/"):
            key = request.headers.get("X-API-Key")
            if not key or not verify_api_key(key):
                return Response("Unauthorized", status_code=401)
        return await call_next(request)

    @app.middleware("http")
    async def rate_limit(request: Request, call_next):
        host = request.client.host if request.client else "anon"
        if request.url.path.startswith("/v1/inbound_call"):
            if not call_limiter.allow(host):
                return Response("Too Many Requests", status_code=429)
        elif request.url.path.startswith("/v1/"):
            if not api_limiter.allow(host + request.url.path):
                return Response("Too Many Requests", status_code=429)
        return await call_next(request)

    @app.get("/v1/login/oauth", summary="Start OAuth login", tags=["auth"])
    async def oauth_login(request: Request):
        state = secrets.token_urlsafe(16)
        request.session["oauth_state"] = state
        url = os.environ.get("OAUTH_AUTH_URL", "https://example.com/auth")
        redirect_url = f"{url}?state={state}"
        return RedirectResponse(redirect_url)

    @app.get("/v1/oauth/callback", summary="Handle OAuth callback", tags=["auth"])
    async def oauth_callback(request: Request):
        try:
            data = OAuthCallbackData(**request.query_params)
        except ValidationError as exc:
            return _json_validation_error(exc)
        if data.state != request.session.pop("oauth_state", None):
            return RedirectResponse("/v1/login/oauth")
        request.session["user"] = data.user or "admin"
        exchange_code(state_manager, data.state, str(request.url))
        return RedirectResponse("/v1/dashboard")

    @app.get("/v1/dashboard", summary="Render call dashboard", tags=["dashboard"])
    async def dashboard(request: Request, q: str | None = None):
        if "user" not in request.session:
            return RedirectResponse("/v1/login/oauth")
        query_param = (q or "").strip()
        with get_session() as session:
            db_query = session.query(Call)
            if query_param:
                from sqlalchemy import or_

                sanitized = re.sub(r"[\s\-()]", "", query_param)
                phone_like = f"{sanitized}%" if sanitized.strip("+").isdigit() else None
                if phone_like:
                    db_query = db_query.filter(
                        or_(
                            Call.from_number.like(phone_like),
                            Call.to_number.like(phone_like),
                            Call.summary.like(f"%{query_param}%"),
                            Call.self_critique.like(f"%{query_param}%"),
                        )
                    )
                else:
                    like = f"%{query_param}%"
                    db_query = db_query.filter(
                        or_(
                            Call.from_number.like(like),
                            Call.to_number.like(like),
                            Call.summary.like(like),
                            Call.self_critique.like(like),
                        )
                    )
            calls = db_query.order_by(Call.created_at.desc()).all()
        body = (
            "\n".join(
                f"<li><a href='/v1/dashboard/{c.id}'>{c.from_number}</a></li>"
                for c in calls
            )
            or "<li>No calls found.</li>"
        )
        html = f"<ul>{body}</ul>"
        return HTMLResponse(html)

    @app.get(
        "/v1/dashboard/{call_id}",
        summary="Dashboard call detail",
        tags=["dashboard"],
    )
    async def dashboard_detail(request: Request, call_id: int):
        if "user" not in request.session:
            return RedirectResponse("/v1/login/oauth")
        with get_session() as session:
            call = session.get(Call, call_id)
        if not call:
            raise HTTPException(status_code=404)
        transcript = Path(call.transcript_path).read_text()
        html = f"<pre>{transcript}</pre>"
        return HTMLResponse(html)

    @app.get(
        "/v1/calls",
        summary="List past calls",
        tags=["calls"],
    )
    async def list_calls(request: Request):
        try:
            params = ListCallsQuery(**request.query_params)
        except (
            ValidationError
        ) as exc:  # pragma: no cover - validated in blueprint tests
            return _json_validation_error(exc)

        with get_session() as session:
            q = session.query(Call)
            if params.phone:
                like = f"%{params.phone}%"
                from sqlalchemy import or_

                q = q.filter(
                    or_(Call.from_number.like(like), Call.to_number.like(like))
                )
            if params.start:
                q = q.filter(Call.created_at >= params.start)
            if params.end:
                q = q.filter(Call.created_at <= params.end)
            if params.error is True:
                q = q.filter(Call.self_critique.is_not(None))
            elif params.error is False:
                q = q.filter(Call.self_critique.is_(None))

            if params.sort.startswith("-"):
                q = q.order_by(Call.created_at.desc())
            else:
                q = q.order_by(Call.created_at.asc())

            total = q.count()
            calls = (
                q.offset((params.page - 1) * params.page_size)
                .limit(params.page_size)
                .all()
            )
            data = [
                CallInfo(
                    id=c.id,
                    call_sid=c.call_sid,
                    from_number=c.from_number,
                    to_number=c.to_number,
                    transcript_path=c.transcript_path,
                    summary=c.summary,
                    self_critique=c.self_critique,
                    created_at=c.created_at,
                )
                for c in calls
            ]
        return {"total": total, "items": data}

    @app.get("/v1/oauth/start", summary="Begin OAuth flow", tags=["auth"])
    async def oauth_start(request: Request):
        try:
            data = OAuthStartData(**request.query_params)
        except ValidationError as exc:
            return _json_validation_error(exc)
        url = generate_auth_url(state_manager, data.user_id or "")
        return RedirectResponse(url)

    @app.post("/v1/inbound_call", summary="Handle inbound call", tags=["calls"])
    @log_call
    async def inbound_call(request: Request):
        try:
            form = await request.form()
            data = InboundCallData(**form)
        except ValidationError as exc:
            return _json_validation_error(exc)

        call_sid = data.CallSid
        state_manager.create_session(call_sid, {"from": data.From, "to": data.To})
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

    @app.post(
        "/v1/recording_status",
        summary="Twilio recording webhook",
        tags=["calls"],
    )
    async def recording_status(request: Request):
        try:
            form = await request.form()
            data = RecordingStatusData(**form)
        except ValidationError as exc:
            return _json_validation_error(exc)

        logger.info(
            "Recording callback: call_sid=%s recording_sid=%s url=%s",
            data.CallSid,
            data.RecordingSid,
            data.RecordingUrl,
        )
        return Response(status_code=204)

    @app.get(
        "/v1/health",
        response_model=dict[str, str],
        summary="Check service health",
        tags=["system"],
    )
    async def health() -> dict[str, str]:
        status: dict[str, str] = {}

        try:
            state_manager._redis.ping()  # type: ignore[attr-defined]
            status["redis"] = "ok"
        except Exception:
            status["redis"] = "error"

        try:
            from sqlalchemy import text

            with get_session() as session:
                session.execute(text("SELECT 1"))
            status["database"] = "ok"
        except Exception:
            status["database"] = "error"

        try:
            state_manager._summary_db.client.heartbeat()  # type: ignore[attr-defined]
            status["chromadb"] = "ok"
        except Exception:
            status["chromadb"] = "error"

        return status

    @app.get("/v1/metrics", summary="Prometheus metrics", tags=["system"])
    async def metrics():
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app
