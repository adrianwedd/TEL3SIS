from __future__ import annotations

import os
from typing import Any, Dict, Optional

import redis


class StateManager:
    """Simple wrapper around Redis for call session state."""

    def __init__(self, url: Optional[str] = None, prefix: str = "session") -> None:
        self.url = url or os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.prefix = prefix
        self._redis = redis.Redis.from_url(self.url, decode_responses=True)

    def _key(self, call_sid: str) -> str:
        return f"{self.prefix}:{call_sid}"

    def create_session(
        self, call_sid: str, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create a new session key with optional initial data."""
        if data is None:
            data = {}
        self._redis.hset(self._key(call_sid), mapping=data)

    def get_session(self, call_sid: str) -> Dict[str, str]:
        """Return all fields for a session."""
        return self._redis.hgetall(self._key(call_sid))

    def update_session(self, call_sid: str, **fields: Any) -> None:
        """Update fields in a session."""
        if fields:
            self._redis.hset(self._key(call_sid), mapping=fields)

    def delete_session(self, call_sid: str) -> None:
        """Remove a session completely."""
        self._redis.delete(self._key(call_sid))
