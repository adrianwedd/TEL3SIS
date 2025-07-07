from __future__ import annotations

import os
from datetime import datetime
from typing import Any, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from server.state_manager import StateManager

__all__ = ["generate_auth_url", "exchange_code", "create_event", "list_events"]

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _build_flow(state: str) -> Any:
    from google_auth_oauthlib.flow import Flow

    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError("Google OAuth client not configured")
    redirect_uri = os.environ.get("BASE_URL", "") + "/oauth/callback"
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
    state_manager: StateManager, user_id: str
) -> Optional[Credentials]:
    data = state_manager.get_token(user_id)
    if not data:
        return None
    creds = Credentials(
        data["access_token"],
        refresh_token=data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ.get("GOOGLE_CLIENT_ID"),
        client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
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
) -> dict:
    """Create a calendar event and return the API response."""
    creds = _get_credentials(state_manager, user_id)
    if not creds:
        raise RuntimeError("No credentials")
    service = build("calendar", "v3", credentials=creds)
    event = {
        "summary": summary,
        "start": {"dateTime": start.isoformat(), "timeZone": timezone},
        "end": {"dateTime": end.isoformat(), "timeZone": timezone},
    }
    return service.events().insert(calendarId="primary", body=event).execute()


def list_events(
    state_manager: StateManager,
    user_id: str,
    time_min: datetime,
    time_max: datetime,
) -> List[dict]:
    """Return upcoming calendar events between two times."""
    creds = _get_credentials(state_manager, user_id)
    if not creds:
        raise RuntimeError("No credentials")
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
