from __future__ import annotations
from datetime import datetime
from typing import Any, List

from google.auth.transport.requests import Request
from .base import Tool
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from loguru import logger

from server.config import Config
from server.state_manager import StateManager
from tools.notifications import send_sms


class AuthError(RuntimeError):
    """Authentication required for the requested action."""


__all__ = [
    "generate_auth_url",
    "exchange_code",
    "create_event",
    "list_events",
    "AuthError",
    "CreateEventTool",
    "ListEventsTool",
]

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _build_flow(state: str) -> Any:
    from google_auth_oauthlib.flow import Flow

    cfg = Config()
    client_id = cfg.google_client_id
    client_secret = cfg.google_client_secret
    if not client_id or not client_secret:
        raise RuntimeError("Google OAuth client not configured")
    redirect_uri = Config().base_url + "/oauth/callback"
    return Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=redirect_uri,
        state=state,
    )


def generate_auth_url(state_manager: StateManager, user_id: str) -> str:
    """Return the Google OAuth consent URL and remember mapping."""
    flow = _build_flow(user_id)
    auth_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true"
    )
    state_manager.set_oauth_state(state, user_id)
    return auth_url


def exchange_code(
    state_manager: StateManager, state: str, authorization_response: str
) -> None:
    """Exchange OAuth callback code for tokens and persist them."""
    user_id = state_manager.pop_oauth_state(state)
    if not user_id:
        raise RuntimeError("Unknown OAuth state")
    flow = _build_flow(state)
    flow.fetch_token(authorization_response=authorization_response)
    creds = flow.credentials
    expires_at = int(creds.expiry.timestamp()) if creds.expiry else None
    state_manager.set_token(user_id, creds.token, creds.refresh_token, expires_at)


def _get_credentials(
    state_manager: StateManager,
    user_id: str,
    user_phone: str | None = None,
    twilio_phone: str | None = None,
) -> Credentials:
    data = state_manager.get_token(user_id)
    if not data:
        if user_phone and twilio_phone:
            url = generate_auth_url(state_manager, user_id)
            send_sms(user_phone, twilio_phone, f"Please authenticate here: {url}")
        raise AuthError("No credentials")
    cfg = Config()
    creds = Credentials(
        data["access_token"],
        refresh_token=data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=cfg.google_client_id,
        client_secret=cfg.google_client_secret,
    )
    if data.get("expires_at"):
        creds.expiry = datetime.fromtimestamp(int(data["expires_at"]))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        expires_at = int(creds.expiry.timestamp()) if creds.expiry else None
        state_manager.set_token(user_id, creds.token, creds.refresh_token, expires_at)
    return creds


def create_event(
    state_manager: StateManager,
    user_id: str,
    summary: str,
    start: datetime,
    end: datetime,
    timezone: str = "UTC",
    *,
    user_phone: str | None = None,
    twilio_phone: str | None = None,
) -> dict:
    """Create a calendar event and return the API response."""
    creds = _get_credentials(state_manager, user_id, user_phone, twilio_phone)
    event = {
        "summary": summary,
        "start": {"dateTime": start.isoformat(), "timeZone": timezone},
        "end": {"dateTime": end.isoformat(), "timeZone": timezone},
    }
    try:
        service = build("calendar", "v3", credentials=creds)
        return service.events().insert(calendarId="primary", body=event).execute()
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to create event for %s: %s", user_id, exc)
        return {"error": "Sorry, I'm unable to create the calendar event right now."}


def list_events(
    state_manager: StateManager,
    user_id: str,
    time_min: datetime,
    time_max: datetime,
    *,
    user_phone: str | None = None,
    twilio_phone: str | None = None,
) -> List[dict]:
    """Return upcoming calendar events between two times."""
    creds = _get_credentials(state_manager, user_id, user_phone, twilio_phone)
    try:
        service = build("calendar", "v3", credentials=creds)
        resp = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return resp.get("items", [])
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to list events for %s: %s", user_id, exc)
        return []


class CreateEventTool(Tool):
    """Tool wrapper around :func:`create_event`."""

    name = "create_event"
    description = "Create an event in the user's Google Calendar."
    parameters = {
        "type": "object",
        "properties": {
            "state_manager": {"type": "object"},
            "user_id": {"type": "string"},
            "summary": {"type": "string"},
            "start": {"type": "string", "format": "date-time"},
            "end": {"type": "string", "format": "date-time"},
            "timezone": {"type": "string", "default": "UTC"},
        },
        "required": ["state_manager", "user_id", "summary", "start", "end"],
    }

    def run(self, **kwargs: Any) -> dict:  # type: ignore[override]
        return create_event(**kwargs)


class ListEventsTool(Tool):
    """Tool wrapper around :func:`list_events`."""

    name = "list_events"
    description = "List calendar events between two times."
    parameters = {
        "type": "object",
        "properties": {
            "state_manager": {"type": "object"},
            "user_id": {"type": "string"},
            "time_min": {"type": "string", "format": "date-time"},
            "time_max": {"type": "string", "format": "date-time"},
        },
        "required": ["state_manager", "user_id", "time_min", "time_max"],
    }

    def run(self, **kwargs: Any) -> List[dict]:  # type: ignore[override]
        return list_events(**kwargs)
