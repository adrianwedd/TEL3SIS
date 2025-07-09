from __future__ import annotations

import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri=os.getenv("RATE_LIMIT_REDIS_URL", "memory://"),
)


def call_rate_limit() -> str:
    return os.getenv("CALL_RATE_LIMIT", "3/minute")


def api_rate_limit() -> str:
    return os.getenv("API_RATE_LIMIT", "60/minute")
