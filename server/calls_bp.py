from __future__ import annotations

import re
from flask import Blueprint, jsonify, request
from .limits import limiter, api_rate_limit

from sqlalchemy import or_

from .database import Call, get_session


bp = Blueprint("calls", __name__)


@bp.get("/v1/calls")
@limiter.limit(api_rate_limit)
def list_calls() -> str:  # type: ignore[return-type]
    """Return JSON list of recorded calls with pagination."""
    filter_val = request.args.get("filter")
    try:
        limit = int(request.args.get("limit", 100))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        limit = 100
        offset = 0
    sort = request.args.get("sort", "-created_at")

    with get_session() as session:
        q = session.query(Call)
        if filter_val:
            sanitized = re.sub(r"[\s\-()]", "", filter_val)
            phone_like = f"{sanitized}%" if sanitized.strip("+").isdigit() else None
            if phone_like:
                q = q.filter(
                    or_(
                        Call.from_number.like(phone_like),
                        Call.to_number.like(phone_like),
                        Call.summary.like(f"%{filter_val}%"),
                        Call.self_critique.like(f"%{filter_val}%"),
                    )
                )
            else:
                like = f"%{filter_val}%"
                q = q.filter(
                    or_(
                        Call.from_number.like(like),
                        Call.to_number.like(like),
                        Call.summary.like(like),
                        Call.self_critique.like(like),
                    )
                )

        field = sort.lstrip("-")
        desc = sort.startswith("-")
        column = getattr(Call, field, None)
        if column is not None:
            q = q.order_by(column.desc() if desc else column.asc())
        else:
            q = q.order_by(Call.created_at.desc())

        calls = q.offset(offset).limit(limit).all()
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
