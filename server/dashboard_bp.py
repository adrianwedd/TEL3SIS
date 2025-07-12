from __future__ import annotations

from pathlib import Path
import re

from flask import (
    Blueprint,
    render_template,
    request,
    abort,
    redirect,
    url_for,
    session,
)
from flask_login import login_required, current_user
from flask_socketio import SocketIO, join_room, leave_room
from sqlalchemy import or_
from pydantic import BaseModel, StrictStr, ValidationError
from collections import defaultdict
from typing import Any, Dict

from .validation import validation_error_response

from .database import Call, get_session
from .recordings import DEFAULT_OUTPUT_DIR
from .tasks import reprocess_call as reprocess_call_task
import secrets

bp = Blueprint("dashboard", __name__, template_folder="templates")
socketio = SocketIO(cors_allowed_origins="*")


def stream_transcript_line(call_sid: str, speaker: str, text: str) -> None:
    """Emit a transcript chunk to all listeners for the call."""
    socketio.emit(
        "transcript_line",
        {"speaker": speaker, "text": text},
        room=call_sid,
    )


@socketio.on("join")
def _join(data: dict[str, str]) -> None:
    call_sid = data.get("call_sid")
    if call_sid:
        join_room(call_sid)


@socketio.on("leave")
def _leave(data: dict[str, str]) -> None:
    call_sid = data.get("call_sid")
    if call_sid:
        leave_room(call_sid)


class DashboardQuery(BaseModel):
    q: StrictStr | None = None


@bp.before_request
def require_login():  # type: ignore[return-type]
    """Redirect anonymous users and setup CSRF token."""
    if not current_user.is_authenticated:
        return redirect(url_for("auth.oauth_login"))
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(16)


@bp.get("/v1/dashboard")
@login_required
def show_dashboard() -> str:  # type: ignore[return-type]
    """Render list of calls with optional search."""
    if current_user.role != "admin":
        abort(403)
    try:
        data = DashboardQuery(**request.args)
    except ValidationError as exc:
        return validation_error_response(exc)
    query_param = (data.q or "").strip()
    with get_session() as session:
        q = session.query(Call)
        if query_param:
            sanitized = re.sub(r"[\s\-()]", "", query_param)
            phone_like = f"{sanitized}%" if sanitized.strip("+").isdigit() else None
            if phone_like:
                q = q.filter(
                    or_(
                        Call.from_number.like(phone_like),
                        Call.to_number.like(phone_like),
                        Call.summary.like(f"%{query_param}%"),
                        Call.self_critique.like(f"%{query_param}%"),
                    )
                )
            else:
                like = f"%{query_param}%"
                q = q.filter(
                    or_(
                        Call.from_number.like(like),
                        Call.to_number.like(like),
                        Call.summary.like(like),
                        Call.self_critique.like(like),
                    )
                )
        calls = q.order_by(Call.created_at.desc()).all()
    return render_template("dashboard/list.html", calls=calls, q=query_param)


@bp.get("/v1/dashboard/<int:call_id>")
@login_required
def call_detail(call_id: int) -> str:  # type: ignore[return-type]
    """Display a single call with transcript and audio."""
    if current_user.role != "admin":
        abort(403)
    with get_session() as session:
        call = session.get(Call, call_id)
        if call is None:
            abort(404)
    transcript = Path(call.transcript_path).read_text()
    audio_filename = Path(call.transcript_path).stem + ".mp3"
    audio_path = f"/recordings/audio/{audio_filename}"
    return render_template(
        "dashboard/detail.html",
        call=call,
        transcript=transcript,
        audio_path=audio_path,
    )


@bp.post("/v1/calls/<int:call_id>/delete")
@login_required
def delete_call(call_id: int) -> str:  # type: ignore[return-type]
    """Remove a call and associated files."""
    if current_user.role != "admin":
        abort(403)
    if request.form.get("csrf_token") != session.get("csrf_token"):
        abort(400)
    with get_session() as session_db:
        call = session_db.get(Call, call_id)
        if call is None:
            abort(404)
        transcript = Path(call.transcript_path)
        audio = DEFAULT_OUTPUT_DIR / f"{transcript.stem}.mp3"
        transcript.unlink(missing_ok=True)
        audio.unlink(missing_ok=True)
        session_db.delete(call)
        session_db.commit()
    return redirect(url_for("dashboard.show_dashboard"))


@bp.post("/v1/calls/<int:call_id>/reprocess")
@login_required
def reprocess_call(call_id: int) -> str:  # type: ignore[return-type]
    """Trigger async re-analysis of a call."""
    if current_user.role != "admin":
        abort(403)
    if request.form.get("csrf_token") != session.get("csrf_token"):
        abort(400)
    reprocess_call_task.delay(call_id)
    return redirect(url_for("dashboard.call_detail", call_id=call_id))


def _aggregate_metrics() -> Dict[str, Any]:
    """Return aggregate call metrics from the database."""
    with get_session() as session:
        calls = session.query(Call).all()

    total = len(calls)
    durations = []
    tools = defaultdict(int)
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


@bp.get("/v1/dashboard/analytics")
@login_required
def analytics() -> str:  # type: ignore[return-type]
    """Render analytics overview for admins."""
    if current_user.role != "admin":
        abort(403)
    metrics = _aggregate_metrics()
    return render_template("dashboard/analytics.html", metrics=metrics)
