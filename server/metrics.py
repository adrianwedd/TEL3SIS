"""Prometheus metrics utilities and FastAPI middleware."""

import time
from contextlib import contextmanager
from typing import Awaitable, Callable

from fastapi import Request, Response
from prometheus_client import Counter, Histogram

__all__ = [
    "http_requests_total",
    "http_request_latency",
    "external_api_calls",
    "external_api_latency",
    "twilio_sms_latency",
    "record_external_api",
    "metrics_middleware",
]

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_latency = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)

external_api_calls = Counter(
    "external_api_calls_total",
    "Total external API calls",
    ["api", "status"],
)

external_api_latency = Histogram(
    "external_api_latency_seconds",
    "External API call latency in seconds",
    ["api"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)

# Specific histogram for Twilio SMS send latency
twilio_sms_latency = Histogram(
    "twilio_sms_latency_seconds",
    "Latency in seconds for sending SMS via Twilio",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)


@contextmanager
def record_external_api(api: str):
    """Context manager to record an external API call."""
    start = time.time()
    try:
        yield
    except Exception:
        external_api_calls.labels(api, "error").inc()
        raise
    else:
        external_api_calls.labels(api, "ok").inc()
    finally:
        external_api_latency.labels(api).observe(time.time() - start)


async def metrics_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Middleware to record HTTP metrics."""
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    endpoint = request.url.path
    http_request_latency.labels(request.method, endpoint).observe(duration)
    http_requests_total.labels(
        request.method, endpoint, str(response.status_code)
    ).inc()
    return response
