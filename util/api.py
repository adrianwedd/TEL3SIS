from __future__ import annotations

from typing import Any, Callable

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

__all__ = ["call_with_retries"]


def call_with_retries(
    func: Callable[..., Any],
    /,
    *args: Any,
    attempts: int = 3,
    wait_seconds: float = 1.0,
    **kwargs: Any,
) -> Any:
    """Call ``func`` with retries and exponential backoff."""

    retryable = retry(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(min=wait_seconds, max=10),
        reraise=True,
    )(func)
    try:
        return retryable(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        name = getattr(func, "__name__", str(func))
        logger.exception("Unrecoverable error in %s: %s", name, exc)
        raise
