from __future__ import annotations

import os
from celery import Celery


def create_celery_app() -> Celery:
    """Create and configure the Celery application."""
    broker = os.getenv(
        "CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://redis:6379/0")
    )
    backend = os.getenv("CELERY_RESULT_BACKEND", broker)
    celery = Celery("tel3sis", broker=broker, backend=backend)

    celery.conf.task_routes = {"server.tasks.*": {"queue": "default"}}
    return celery


celery_app = create_celery_app()
