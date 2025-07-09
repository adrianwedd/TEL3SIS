from __future__ import annotations

from flask import Blueprint, jsonify
from .limits import limiter, api_rate_limit

from .database import Call, get_session


bp = Blueprint("calls", __name__)


@bp.get("/v1/calls")
@limiter.limit(api_rate_limit)
def list_calls() -> str:  # type: ignore[return-type]
    """Return JSON list of recorded calls."""
    with get_session() as session:
        calls = session.query(Call).order_by(Call.created_at.desc()).all()
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
    return jsonify(data)
