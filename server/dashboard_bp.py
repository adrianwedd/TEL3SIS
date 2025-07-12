from __future__ import annotations

from pathlib import Path
import re

from flask import Blueprint, render_template, request, abort, redirect, url_for
from flask_login import login_required, current_user
from flask_socketio import SocketIO, join_room, leave_room
from sqlalchemy import or_
from pydantic import BaseModel, StrictStr, ValidationError

from .validation import validation_error_response

from .database import Call, get_session

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
    filter: StrictStr | None = None
    q: StrictStr | None = None
    limit: int = 20
    offset: int = 0
    sort: StrictStr = "-created_at"


@bp.before_request
def require_login():  # type: ignore[return-type]
    """Redirect anonymous users to OAuth login."""
    if not current_user.is_authenticated:
        return redirect(url_for("auth.oauth_login"))


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
    query_param = (data.filter or data.q or "").strip()
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

        field = data.sort.lstrip("-")
        desc_sort = data.sort.startswith("-")
        column = getattr(Call, field, None)
        if column is not None:
            q = q.order_by(column.desc() if desc_sort else column.asc())
        else:
            q = q.order_by(Call.created_at.desc())

        total = q.count()
        calls = q.offset(data.offset).limit(data.limit).all()

    next_offset = data.offset + data.limit if data.offset + data.limit < total else None
    prev_offset = data.offset - data.limit if data.offset > 0 else None

    return render_template(
        "dashboard/list.html",
        calls=calls,
        filter=query_param,
        limit=data.limit,
        offset=data.offset,
        sort=data.sort,
        next_offset=next_offset,
        prev_offset=prev_offset,
    )


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
