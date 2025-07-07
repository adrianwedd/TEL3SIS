from __future__ import annotations

from celery.utils.log import get_task_logger
from pathlib import Path

from .recordings import transcribe_recording

from .celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task
def echo(message: str) -> str:
    """Simple debug task that echoes the incoming message."""
    logger.info("Echoing: %s", message)
    return message


@celery_app.task
def transcribe_audio(audio_path: str) -> str:
    """Transcribe an audio file and return the transcript path."""

    path = transcribe_recording(Path(audio_path))
    logger.info("Transcribed %s", audio_path)
    return str(path)
