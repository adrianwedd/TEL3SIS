from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import or_
from .limits import limiter, api_rate_limit

from .database import Call, get_session


bp = Blueprint("calls", __name__)


class ListCallsQuery(BaseModel):
    """Parameters for filtering and paginating call history."""

    start: datetime | None = None
    end: datetime | None = None
    phone: str | None = None
    error: bool | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort: str = "-timestamp"


@bp.get("/v1/calls")
@limiter.limit(api_rate_limit)
def list_calls() -> str:  # type: ignore[return-type]
    """Return JSON list of recorded calls."""
    try:
        params = ListCallsQuery(**request.args)
    except ValidationError as exc:  # pragma: no cover - validated in app tests
        return jsonify({"error": "invalid_request", "details": exc.errors()}), 400

    with get_session() as session:
        q = session.query(Call)
        if params.phone:
            like = f"%{params.phone}%"
            q = q.filter(or_(Call.from_number.like(like), Call.to_number.like(like)))
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
            q.offset((params.page - 1) * params.page_size).limit(params.page_size).all()
        )

        data = [
            {
                "id": c.id,
                "call_sid": c.call_sid,
                "from_number": c.from_number,
                "to_number": c.to_number,
                "transcript_path": c.transcript_path,
                "summary": c.summary,
                "self_critique": c.self_critique,
                "created_at": c.created_at.isoformat(),
            }
            for c in calls
        ]

    return jsonify({"total": total, "items": data})
