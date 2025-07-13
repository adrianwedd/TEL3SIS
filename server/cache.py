import hashlib
import json
from functools import wraps
from typing import Any, Callable

import redis

from .config import Config

__all__ = ["redis_cache", "clear_cache"]

_redis = redis.Redis.from_url(Config().redis_url, decode_responses=True)


def _make_key(prefix: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    payload = json.dumps({"a": args, "k": kwargs}, sort_keys=True, default=str)
    digest = hashlib.sha256(payload.encode()).hexdigest()
    return f"cache:{prefix}:{digest}"


def redis_cache(ttl: int = 3600) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Cache the result of a function in Redis for ``ttl`` seconds."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        prefix = f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = _make_key(prefix, args, kwargs)
            cached = _redis.get(key)
            if cached is not None:
                return json.loads(cached)
            result = func(*args, **kwargs)
            try:
                _redis.setex(key, ttl, json.dumps(result))
            except Exception:  # noqa: BLE001
                pass
            return result

        return wrapper

    return decorator


def clear_cache(pattern: str = "cache:*") -> int:
    """Delete cache keys matching ``pattern`` and return number removed."""
    keys = _redis.keys(pattern)
    if keys:
        _redis.delete(*keys)
    return len(keys)
