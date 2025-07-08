from __future__ import annotations

from celery.utils.log import get_task_logger
from pathlib import Path

from .recordings import transcribe_recording
from tools.notifications import send_email
from .database import save_call_summary
from .self_reflection import generate_self_critique

from .celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task
def echo(message: str) -> str:
    """Simple debug task that echoes the incoming message."""
    logger.info("Echoing: %s", message)
    return message


@celery_app.task
def summarize_text(text: str, max_words: int = 30) -> str:
    """Return a naive summary consisting of the first ``max_words``."""

    words = text.strip().split()
    return " ".join(words[:max_words])


def transcribe_audio(
    audio_path: str,
    call_sid: str,
    from_number: str,
    to_number: str,
) -> str:
    """Transcribe an audio file and persist a summary."""

    path = transcribe_recording(Path(audio_path))
    logger.info("Transcribed %s", audio_path)
    send_transcript_email.delay(str(path))
    text = Path(path).read_text()
    summary = summarize_text(text)
    critique = generate_self_critique(text)
    save_call_summary(
        call_sid,
        from_number,
        to_number,
        str(path),
        summary,
        critique,
    )
    return str(path)


@celery_app.task
def send_transcript_email(transcript_path: str, to_email: str | None = None) -> None:
    """Send the transcript file via email."""
    send_email(transcript_path, to_email)
