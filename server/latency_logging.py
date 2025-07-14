from __future__ import annotations

import asyncio
import time
from typing import Any, Callable

from logging_config import logger
from prometheus_client import Histogram

# Histograms for latency metrics indexed by step name
_histograms: dict[str, Histogram] = {}


def _get_histogram(step_name: str) -> Histogram:
    """Return (and lazily create) a Histogram for the given step."""
    if step_name not in _histograms:
        _histograms[step_name] = Histogram(
            f"{step_name}_latency_seconds",
            f"Latency in seconds for {step_name} step",
            buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        )
    return _histograms[step_name]


def _log_event(event: str, call_sid: str | None, **extra: Any) -> None:
    """Emit a structured log line."""
    logger.bind(event=event, call_sid=call_sid, **extra).info("latency")


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
                latency = end - start
                _get_histogram(step_name).observe(latency)
                _log_event(
                    f"{step_name}_end",
                    call_sid,
                    latency_ms=int(latency * 1000),
                    timestamp=end,
                )
                return result

            return async_wrapper

        def sync_wrapper(*args: Any, call_sid: str | None = None, **kwargs: Any) -> Any:
            start = time.time()
            _log_event(f"{step_name}_start", call_sid, timestamp=start)
            result = func(*args, **kwargs)
            end = time.time()
            latency = end - start
            _get_histogram(step_name).observe(latency)
            _log_event(
                f"{step_name}_end",
                call_sid,
                latency_ms=int(latency * 1000),
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


def log_call(func: Callable[..., Any]) -> Callable[..., Any]:
    """Measure overall call handling latency."""
    return log_vocode_step("call")(func)
