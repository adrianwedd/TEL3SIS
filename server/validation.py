from __future__ import annotations

from flask import jsonify, Response as FlaskResponse
from pydantic import ValidationError


__all__ = ["validation_error_response"]


def validation_error_response(exc: ValidationError) -> FlaskResponse:
    """Return a JSON error response for request validation failures."""
    resp = jsonify({"error": "invalid_request", "details": exc.errors()})
    resp.status_code = 400
    return resp  # type: ignore[return-value]
