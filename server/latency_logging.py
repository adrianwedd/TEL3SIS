from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Callable

from loguru import logger


def _log_event(event: str, call_sid: str | None, **extra: Any) -> None:
    """Emit a structured log line in JSON."""
    payload = {"event": event, "call_sid": call_sid, **extra}
    logger.info(json.dumps(payload))


def log_vocode_step(
    step_name: str,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorate a handler to measure latency and log start/end events."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(
                *args: Any, call_sid: str | None = None, **kwargs: Any
            ) -> Any:
                start = time.time()
                _log_event(f"{step_name}_start", call_sid, timestamp=start)
                result = await func(*args, **kwargs)
                end = time.time()
                _log_event(
                    f"{step_name}_end",
                    call_sid,
                    latency_ms=int((end - start) * 1000),
                    timestamp=end,
                )
                return result

            return async_wrapper

        def sync_wrapper(*args: Any, call_sid: str | None = None, **kwargs: Any) -> Any:
            start = time.time()
            _log_event(f"{step_name}_start", call_sid, timestamp=start)
            result = func(*args, **kwargs)
            end = time.time()
            _log_event(
                f"{step_name}_end",
                call_sid,
                latency_ms=int((end - start) * 1000),
                timestamp=end,
            )
            return result

        return sync_wrapper

    return decorator


# Convenience wrappers -------------------------------------------------------


def log_stt(func: Callable[..., Any]) -> Callable[..., Any]:
    return log_vocode_step("stt")(func)


def log_llm(func: Callable[..., Any]) -> Callable[..., Any]:
    return log_vocode_step("llm")(func)


def log_tts(func: Callable[..., Any]) -> Callable[..., Any]:
    return log_vocode_step("tts")(func)
