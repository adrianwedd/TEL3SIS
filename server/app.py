"""FastAPI application serving telephony and web endpoints."""
from __future__ import annotations
import re
import secrets
from pathlib import Path
from collections import defaultdict
from typing import Any
import asyncio

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    Response,
    Depends,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from apispec import APISpec
from pydantic import BaseModel, Field, HttpUrl, ValidationError
from sqlalchemy import select, func
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
    User,
    get_session_async,
    get_user_preference_async,
    init_db_async,
    set_user_preference_async,
    verify_api_key_async,
    get_agent_config_async,
    update_agent_config_async,
)
from .settings import Settings, ConfigError
from .handoff import dial_twiml
from .state_manager import StateManager
from .tasks import echo, reprocess_call, delete_call_record, process_recording
from agents.sms_agent import SMSAgent
from tools.notifications import send_sms
from tools.calendar import exchange_code, generate_auth_url, SCOPES
from agents.core_agent import (
    build_core_agent,
    SafeAgentFactory,
    SafeFunctionCallingAgent,
)
from .chat import manager as chat_manager, uuid4
from .latency_logging import log_call
from .metrics import metrics_middleware


class AgentConfigPayload(BaseModel):
    prompt: str = ""
    voice: str = ""


class InboundCallData(BaseModel):
    CallSid: str
    From: str
    To: str
    SpeechResult: str | None = None


class RecordingStatusData(BaseModel):
    CallSid: str
    RecordingSid: str
    RecordingUrl: HttpUrl


class InboundSMSData(BaseModel):
    """Data payload for Twilio SMS webhooks."""

    MessageSid: str
    From: str
    To: str
    Body: str


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


class SearchQuery(BaseModel):
    """Parameters for search endpoint."""

    q: str
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


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


async def _aggregate_metrics() -> dict[str, Any]:
    """Return aggregate call metrics from the database."""
    async with get_session_async() as session:
        result = await session.execute(select(Call))
        calls = result.scalars().all()

    total = len(calls)
    durations: list[float] = []
    tools: dict[str, int] = defaultdict(int)
    for call in calls:
        try:
            text = Path(call.transcript_path).read_text()
        except Exception:
            text = ""
        durations.append(len(text.split()) / 2)
        text_lower = f"{text.lower()} {(call.summary or '').lower()}"
        for name in ["weather", "calendar", "sms", "email"]:
            if name in text_lower:
                tools[name] += 1

    avg_duration = sum(durations) / total if total else 0.0
    return {
        "total_calls": total,
        "avg_duration": avg_duration,
        "tool_usage": dict(tools),
    }


async def _check_admin(username: str) -> bool:
    """Return True if ``username`` has admin role."""
    async with get_session_async() as session:
        result = await session.execute(select(User).filter_by(username=username))
        user = result.scalar_one_or_none()
        return bool(user and user.role == "admin")


def _require_user(request: Request) -> str:
    """Return the logged in username or raise 401."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401)
    return str(user)


def create_app(cfg: Settings | None = None) -> FastAPI:
    try:
        config = cfg or Settings()
    except ConfigError as exc:
        raise RuntimeError(str(exc)) from exc

    app = FastAPI(
        title="TEL3SIS API",
        version="1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )
    app.middleware("http")(metrics_middleware)
    templates = Jinja2Templates(directory="server/templates")
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

    asyncio.run(init_db_async())

    call_limit, call_interval = _parse_rate(config.call_rate_limit)
    api_limit, api_interval = _parse_rate(config.api_rate_limit)
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
            if not key or not await verify_api_key_async(key):
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
        """Begin the OAuth login flow.

        Example:
            ``GET /v1/login/oauth`` redirects the browser to the provider.
        """
        state = secrets.token_urlsafe(16)
        request.session["oauth_state"] = state
        url = config.oauth_auth_url
        redirect_url = f"{url}?state={state}"
        return RedirectResponse(redirect_url)

    @app.get("/v1/oauth/callback", summary="Handle OAuth callback", tags=["auth"])
    async def oauth_callback(request: Request):
        """Process the OAuth provider redirect and finalize login.

        Example:
            ``GET /v1/oauth/callback?state=xyz&user=u`` stores the session and
            redirects to ``/v1/dashboard``.
        """
        try:
            data = OAuthCallbackData(**request.query_params)
        except ValidationError as exc:
            return _json_validation_error(exc)
        if data.state != request.session.pop("oauth_state", None):
            return RedirectResponse("/v1/login/oauth")
        request.session["user"] = data.user or "admin"
        exchange_code(state_manager, data.state, str(request.url))
        return RedirectResponse("/v1/dashboard")

    @app.get(
        "/v1/dashboard",
        summary="Render call dashboard",
        tags=["dashboard"],
        name="dashboard.show_dashboard",
    )
    async def dashboard(
        request: Request,
        q: str | None = None,
        user: str = Depends(_require_user),
    ):
        """Show a list of processed calls.

        Example:
            ``GET /v1/dashboard?q=+1555`` filters by phone number.
        """
        query_param = (q or "").strip()
        async with get_session_async() as session:
            db_query = select(Call)
            if query_param:
                from sqlalchemy import or_

                sanitized = re.sub(r"[\s\-()]", "", query_param)
                phone_like = f"{sanitized}%" if sanitized.strip("+").isdigit() else None
                if phone_like:
                    db_query = db_query.where(
                        or_(
                            Call.from_number.like(phone_like),
                            Call.to_number.like(phone_like),
                            Call.summary.like(f"%{query_param}%"),
                            Call.self_critique.like(f"%{query_param}%"),
                        )
                    )
                else:
                    like = f"%{query_param}%"
                    db_query = db_query.where(
                        or_(
                            Call.from_number.like(like),
                            Call.to_number.like(like),
                            Call.summary.like(like),
                            Call.self_critique.like(like),
                        )
                    )
            result = await session.execute(db_query.order_by(Call.created_at.desc()))
            calls = result.scalars().all()
        return templates.TemplateResponse(
            "dashboard/list.html",
            {"request": request, "calls": calls, "q": query_param},
        )

    @app.get(
        "/v1/dashboard/{call_id}",
        summary="Dashboard call detail",
        tags=["dashboard"],
        name="dashboard.call_detail",
    )
    async def dashboard_detail(
        request: Request,
        call_id: int,
        user: str = Depends(_require_user),
    ):
        """Render detail page for a single call.

        Example:
            ``GET /v1/dashboard/42`` returns HTML with transcript and audio.
        """
        async with get_session_async() as session:
            call = await session.get(Call, call_id)
        if not call:
            raise HTTPException(status_code=404)
        transcript = Path(call.transcript_path).read_text()
        audio_path = f"/recordings/audio/{Path(call.transcript_path).stem}.mp3"
        return templates.TemplateResponse(
            "dashboard/detail.html",
            {
                "request": request,
                "call": call,
                "transcript": transcript,
                "audio_path": audio_path,
            },
        )

    @app.get(
        "/v1/dashboard/analytics",
        summary="Analytics overview",
        tags=["dashboard"],
        name="dashboard.analytics",
    )
    async def dashboard_analytics(
        request: Request,
        user: str = Depends(_require_user),
    ):
        """Show aggregated call metrics."""
        metrics = await _aggregate_metrics()
        return templates.TemplateResponse(
            "dashboard/analytics.html",
            {"request": request, "metrics": metrics},
        )

    @app.post(
        "/v1/dashboard/{call_id}/delete",
        summary="Delete call record",
        tags=["dashboard"],
        name="dashboard.delete_call",
    )
    async def dashboard_delete_call(
        request: Request,
        call_id: int,
        user: str = Depends(_require_user),
    ):
        """Delete a call record asynchronously."""
        if not await _check_admin(request.session["user"]):
            raise HTTPException(status_code=403)
        delete_call_record.delay(call_id)
        url = app.url_path_for("dashboard.show_dashboard")
        return RedirectResponse(url, status_code=303)

    @app.post(
        "/v1/dashboard/{call_id}/reprocess",
        summary="Reprocess call record",
        tags=["dashboard"],
        name="dashboard.reprocess_call",
    )
    async def dashboard_reprocess_call(
        request: Request,
        call_id: int,
        user: str = Depends(_require_user),
    ):
        """Queue a call for reprocessing."""
        if not await _check_admin(request.session["user"]):
            raise HTTPException(status_code=403)
        reprocess_call.delay(call_id)
        url = app.url_path_for("dashboard.call_detail", call_id=call_id)
        return RedirectResponse(url, status_code=303)

    @app.get(
        "/v1/calls",
        summary="List past calls",
        tags=["calls"],
    )
    async def list_calls(
        request: Request,
        user: str = Depends(_require_user),
    ):
        """Return paginated call history as JSON."""
        try:
            params = ListCallsQuery(**request.query_params)
        except ValidationError as exc:  # pragma: no cover - validated in API tests
            return _json_validation_error(exc)

        async with get_session_async() as session:
            q = select(Call)
            if params.phone:
                like = f"%{params.phone}%"
                from sqlalchemy import or_

                q = q.where(or_(Call.from_number.like(like), Call.to_number.like(like)))
            if params.start:
                q = q.where(Call.created_at >= params.start)
            if params.end:
                q = q.where(Call.created_at <= params.end)
            if params.error is True:
                q = q.where(Call.self_critique.is_not(None))
            elif params.error is False:
                q = q.where(Call.self_critique.is_(None))

            if params.sort.startswith("-"):
                q = q.order_by(Call.created_at.desc())
            else:
                q = q.order_by(Call.created_at.asc())
            result_total = await session.execute(
                select(func.count()).select_from(q.subquery())
            )
            total = result_total.scalar_one()
            result = await session.execute(
                q.offset((params.page - 1) * params.page_size).limit(params.page_size)
            )
            calls = result.scalars().all()
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

    @app.get(
        "/v1/search",
        summary="Keyword search over call history",
        tags=["calls"],
    )
    async def search_calls(
        request: Request,
        user: str = Depends(_require_user),
    ):
        """Search transcripts and summaries by keyword."""
        try:
            params = SearchQuery(**request.query_params)
        except ValidationError as exc:
            return _json_validation_error(exc)

        query = params.q.strip()
        async with get_session_async() as session:
            db_query = select(Call)
            if query:
                from sqlalchemy import or_

                sanitized = re.sub(r"[\s\-()]", "", query)
                phone_like = (
                    f"%{sanitized}%" if sanitized.strip("+").isdigit() else None
                )
                like = f"%{query}%"
                filters = [Call.summary.like(like), Call.self_critique.like(like)]
                if phone_like:
                    filters.extend(
                        [
                            Call.from_number.like(phone_like),
                            Call.to_number.like(phone_like),
                        ]
                    )
                db_query = db_query.where(or_(*filters))
            result = await session.execute(db_query.order_by(Call.created_at.desc()))
            calls = result.scalars().all()

        matches: list[Call] = []
        q_lower = query.lower()
        sanitized = re.sub(r"[\s\-()]", "", query)
        for call in calls:
            text = ""
            try:
                text = Path(call.transcript_path).read_text().lower()
            except Exception:
                pass
            if (
                q_lower in text
                or q_lower in (call.summary or "").lower()
                or q_lower in (call.self_critique or "").lower()
                or sanitized
                in re.sub(r"[\s\-()]", "", call.from_number + call.to_number)
            ):
                matches.append(call)

        total = len(matches)
        start = (params.page - 1) * params.page_size
        subset = matches[start : start + params.page_size]
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
            for c in subset
        ]
        return {"total": total, "items": data}

    @app.get(
        "/v1/admin/conversations/{call_id}",
        summary="Retrieve conversation logs",
        tags=["admin"],
    )
    async def get_conversation_log(
        call_id: int,
        user: str = Depends(_require_user),
    ) -> dict:
        """Return transcript and metadata for a call."""
        async with get_session_async() as session:
            call = await session.get(Call, call_id)
        if not call:
            raise HTTPException(status_code=404)
        transcript = Path(call.transcript_path).read_text()
        return {
            "call_sid": call.call_sid,
            "from_number": call.from_number,
            "to_number": call.to_number,
            "summary": call.summary,
            "self_critique": call.self_critique,
            "transcript": transcript,
            "created_at": call.created_at.isoformat(),
        }

    @app.get(
        "/v1/admin/agent_status",
        summary="Current agent status",
        tags=["admin"],
    )
    async def agent_status(user: str = Depends(_require_user)) -> dict:
        """Return counts of active sessions and websockets."""
        sessions = []
        try:
            sessions = state_manager.list_sessions()
        except Exception:
            pass
        return {
            "active_sessions": len(sessions),
            "active_websockets": len(chat_manager.active),
        }

    @app.get("/v1/admin/config", summary="Get agent config", tags=["admin"])
    async def get_config(user: str = Depends(_require_user)) -> AgentConfigPayload:
        """Return the editable prompt and voice settings."""
        data = await get_agent_config_async()
        return AgentConfigPayload(
            prompt=data.get("prompt", ""), voice=data.get("voice", "")
        )

    @app.put(
        "/v1/admin/config",
        summary="Update agent config",
        tags=["admin"],
        status_code=204,
    )
    async def update_config(
        payload: AgentConfigPayload, user: str = Depends(_require_user)
    ) -> Response:
        """Persist new agent configuration."""
        await update_agent_config_async(prompt=payload.prompt, voice=payload.voice)
        return Response(status_code=204)

    @app.get(
        "/v1/oauth/consent",
        summary="Explain OAuth permissions",
        tags=["auth"],
    )
    async def oauth_consent(request: Request):
        """Render a consent page outlining required OAuth scopes."""
        data = OAuthStartData(**request.query_params)
        return templates.TemplateResponse(
            "oauth_consent.html",
            {"request": request, "user_id": data.user_id or "", "scopes": SCOPES},
        )

    @app.get("/v1/oauth/start", summary="Begin OAuth flow", tags=["auth"])
    async def oauth_start(request: Request):
        """Generate the provider authorization URL."""
        try:
            data = OAuthStartData(**request.query_params)
        except ValidationError as exc:
            return _json_validation_error(exc)
        url = generate_auth_url(state_manager, data.user_id or "")
        return RedirectResponse(url)

    @app.post("/v1/inbound_call", summary="Handle inbound call", tags=["calls"])
    @log_call
    async def inbound_call(request: Request):
        """Entry point for Twilio voice webhooks."""
        try:
            form = await request.form()
            data = InboundCallData(**form)
        except ValidationError as exc:
            return _json_validation_error(exc)

        call_sid = data.CallSid
        state_manager.create_session(call_sid, {"from": data.From, "to": data.To})
        echo.delay(f"Call {call_sid} started")

        language = await get_user_preference_async(data.From, "language")
        if not language and data.SpeechResult:
            from tools.language import detect_language

            language = detect_language(data.SpeechResult)
            await set_user_preference_async(data.From, "language", language)
        if not language:
            from tools.language import guess_language_from_number

            language = guess_language_from_number(data.From)
            await set_user_preference_async(data.From, "language", language)
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
                to_phone=config.escalation_phone_number,
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

    async def _handle_sms_webhook(request: Request) -> Response:
        """Process Twilio SMS webhook payload and respond."""
        try:
            form = await request.form()
            data = InboundSMSData(**form)
        except ValidationError as exc:
            return _json_validation_error(exc)

        sms_id = data.MessageSid
        state_manager.create_session(sms_id, {"from": data.From, "to": data.To})
        agent = SMSAgent(state_manager, sms_id)
        response_text = await agent.handle_message(data.Body)
        send_sms(data.From, data.To, response_text)
        return Response(status_code=204)

    @app.post("/v1/inbound_sms", summary="Handle inbound SMS", tags=["sms"])
    async def inbound_sms(request: Request):
        """Handle a user SMS message and respond via agent."""
        return await _handle_sms_webhook(request)

    @app.post("/v1/sms/webhook", summary="Twilio SMS webhook", tags=["sms"])
    async def sms_webhook(request: Request):
        """Alias for Twilio's SMS webhook configuration."""
        return await _handle_sms_webhook(request)

    @app.post(
        "/v1/recording_status",
        summary="Twilio recording webhook",
        tags=["calls"],
    )
    async def recording_status(request: Request):
        """Receive a notification that call audio is ready."""
        try:
            form = await request.form()
            data = RecordingStatusData(**form)
        except ValidationError as exc:
            return _json_validation_error(exc)

        logger.bind(
            call_sid=data.CallSid,
            recording_sid=data.RecordingSid,
            url=str(data.RecordingUrl),
        ).info("recording_callback")
        session = state_manager.get_session(data.CallSid)
        process_recording.delay(
            data.RecordingUrl,
            data.CallSid,
            session.get("from", ""),
            session.get("to", ""),
        )
        return Response(status_code=204)

    @app.websocket("/chat/ws")
    async def chat_ws(websocket: WebSocket, session_id: str | None = None):
        """Bidirectional WebSocket chat with the core agent.

        Example:
            ``websocket /chat/ws`` establishes a session and streams responses
            as the user sends messages.
        """

        sid = session_id or str(uuid4())
        await chat_manager.connect(sid, websocket)
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

    @app.get(
        "/v1/health",
        response_model=dict[str, str],
        summary="Check service health",
        tags=["system"],
    )
    async def health() -> dict[str, str]:
        """Return connectivity status for subsystems."""
        status: dict[str, str] = {}

        try:
            state_manager._redis.ping()  # type: ignore[attr-defined]
            status["redis"] = "ok"
        except Exception:
            status["redis"] = "error"

        try:
            from sqlalchemy import text

            async with get_session_async() as session:
                await session.execute(text("SELECT 1"))
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
        """Expose Prometheus metrics for scraping."""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app
