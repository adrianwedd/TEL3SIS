"""Prometheus metrics utilities and FastAPI middleware."""

import time
from contextlib import contextmanager
from typing import Awaitable, Callable, Dict, Optional
from datetime import datetime, timedelta

from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge, Info
from logging_config import logger

__all__ = [
    "http_requests_total",
    "http_request_latency",
    "external_api_calls",
    "external_api_latency",
    "twilio_sms_latency",
    "record_external_api",
    "metrics_middleware",
    # Business metrics
    "call_duration",
    "call_outcomes",
    "tool_usage",
    "conversation_turns",
    "user_satisfaction",
    "agent_performance",
    "system_health",
    "record_call_metrics",
    "record_conversation_metrics",
    "record_business_metrics",
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

# Business Metrics
call_duration = Histogram(
    "tel3sis_call_duration_seconds",
    "Duration of phone calls in seconds",
    ["outcome", "language"],
    buckets=(5, 15, 30, 60, 120, 300, 600, 1800),
)

call_outcomes = Counter(
    "tel3sis_call_outcomes_total",
    "Total call outcomes by type",
    ["outcome", "language", "user_type"],
)

tool_usage = Counter(
    "tel3sis_tool_usage_total",
    "Tool usage frequency",
    ["tool_name", "outcome", "user_type"],
)

conversation_turns = Histogram(
    "tel3sis_conversation_turns",
    "Number of turns in a conversation",
    ["language", "outcome"],
    buckets=(1, 3, 5, 10, 20, 50, 100),
)

user_satisfaction = Gauge(
    "tel3sis_user_satisfaction_score",
    "User satisfaction score (0-10)",
    ["language", "call_type"],
)

agent_performance = Histogram(
    "tel3sis_agent_response_time_seconds",
    "Agent response generation time",
    ["agent_type", "tool_used"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
)

system_health = Gauge(
    "tel3sis_system_health_score",
    "Overall system health indicator (0-1)",
    ["component"],
)


@contextmanager
def record_external_api(api: str, user_type: str = "unknown"):
    """Context manager to record an external API call with business context."""
    start = time.time()
    try:
        yield
    except Exception:
        external_api_calls.labels(api, "error").inc()
        tool_usage.labels(api, "error", user_type).inc()
        raise
    else:
        external_api_calls.labels(api, "ok").inc()
        tool_usage.labels(api, "success", user_type).inc()
    finally:
        external_api_latency.labels(api).observe(time.time() - start)


def record_call_metrics(
    duration: float,
    outcome: str,
    language: str = "en",
    user_type: str = "standard",
    turns: int = 0,
    satisfaction_score: Optional[float] = None,
) -> None:
    """Record comprehensive call metrics."""
    try:
        call_duration.labels(outcome, language).observe(duration)
        call_outcomes.labels(outcome, language, user_type).inc()
        
        if turns > 0:
            conversation_turns.labels(language, outcome).observe(turns)
        
        if satisfaction_score is not None:
            user_satisfaction.labels(language, "voice_call").set(satisfaction_score)
    except Exception as exc:
        logger.bind(error=str(exc)).warning("failed_to_record_call_metrics")


def record_conversation_metrics(
    agent_response_time: float,
    agent_type: str = "core_agent",
    tool_used: str = "none",
) -> None:
    """Record conversation-level metrics."""
    try:
        agent_performance.labels(agent_type, tool_used).observe(agent_response_time)
    except Exception as exc:
        logger.bind(error=str(exc)).warning("failed_to_record_conversation_metrics")


def record_business_metrics(
    system_health_scores: Optional[Dict[str, float]] = None,
) -> None:
    """Record high-level business metrics."""
    try:
        if system_health_scores:
            for component, score in system_health_scores.items():
                system_health.labels(component).set(score)
                
    except Exception as exc:
        logger.bind(error=str(exc)).warning("failed_to_record_business_metrics")


async def metrics_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Middleware to record HTTP metrics with enhanced business context."""
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    endpoint = request.url.path
    # Normalize endpoint for better metrics grouping
    normalized_endpoint = _normalize_endpoint(endpoint)
    
    http_request_latency.labels(request.method, normalized_endpoint).observe(duration)
    http_requests_total.labels(
        request.method, normalized_endpoint, str(response.status_code)
    ).inc()
    
    return response


def _normalize_endpoint(path: str) -> str:
    """Normalize API endpoints for better metric grouping."""
    import re
    # Replace UUIDs and IDs with placeholders
    path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{uuid}', path)
    path = re.sub(r'/\d+', '/{id}', path)
    return path
