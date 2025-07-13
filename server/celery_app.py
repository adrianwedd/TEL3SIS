from __future__ import annotations
from celery import Celery
from celery.schedules import crontab

from server.settings import Settings


def create_celery_app(cfg: Settings | None = None) -> Celery:
    """Create and configure the Celery application."""
    cfg = cfg or Settings()
    broker = cfg.celery_broker_url
    backend = cfg.celery_result_backend
    celery = Celery("tel3sis", broker=broker, backend=backend)

    celery.conf.task_routes = {"server.tasks.*": {"queue": "default"}}
    celery.conf.beat_schedule = {
        "cleanup-old-calls": {
            "task": "server.tasks.cleanup_old_calls",
            "schedule": crontab(minute=0, hour=0),
        },
        "backup-data": {
            "task": "server.tasks.backup_data",
            "schedule": crontab(minute=0, hour=1),
        },
        "refresh-tokens": {
            "task": "server.tasks.refresh_tokens_task",
            "schedule": crontab(minute="*/10"),
        },
    }
    return celery


celery_app = create_celery_app()
