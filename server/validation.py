from __future__ import annotations

from fastapi.responses import JSONResponse
from pydantic import ValidationError


__all__ = ["validation_error_response"]


def validation_error_response(exc: ValidationError) -> JSONResponse:
    """Return a JSON error response for request validation failures."""
    return JSONResponse(
        {"error": "invalid_request", "details": exc.errors()}, status_code=400
    )
