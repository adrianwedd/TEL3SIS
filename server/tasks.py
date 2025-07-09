from __future__ import annotations

from logging_config import logger
from pathlib import Path

from datetime import datetime, timedelta, UTC
from .recordings import transcribe_recording, DEFAULT_OUTPUT_DIR
import tools.notifications as notifications
from .database import (
    save_call_summary,
    get_session,
    Call,
    set_user_preference,
)
from .self_reflection import generate_self_critique
from tools.language import detect_language

from .celery_app import celery_app


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
    sanitized = notifications.sanitize_transcript(text)
    logger.debug("Transcript sanitized snippet: %s", sanitized[:100])
    language = detect_language(text)
    set_user_preference(from_number, "language", language)
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
    notifications.send_email(transcript_path, to_email)


@celery_app.task
def cleanup_old_calls(days: int = 30) -> int:
    """Delete call records and files older than ``days`` days."""

    cutoff = datetime.now(UTC) - timedelta(days=days)
    removed = 0
    with get_session() as session:
        old_calls = session.query(Call).filter(Call.created_at < cutoff).all()
        for call in old_calls:
            transcript = Path(call.transcript_path)
            audio = DEFAULT_OUTPUT_DIR / f"{transcript.stem}.mp3"
            transcript.unlink(missing_ok=True)
            audio.unlink(missing_ok=True)
            session.delete(call)
            removed += 1
        session.commit()
    return removed
