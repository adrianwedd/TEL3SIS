from __future__ import annotations

from logging_config import logger
from pathlib import Path

from datetime import datetime, timedelta, UTC
import os
import tarfile

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

try:  # pragma: no cover - optional dependency
    import boto3
except Exception:  # pragma: no cover - boto3 may not be installed
    boto3 = None


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


@celery_app.task
def backup_data(upload_to_s3: bool | None = None) -> str:
    """Create a compressed backup of the SQLite DB and vector store."""

    db_url = os.getenv("DATABASE_URL", "sqlite:///tel3sis.db")
    if not db_url.startswith("sqlite:///"):
        raise ValueError("Only SQLite DATABASE_URL supported")
    db_path = Path(db_url.split("sqlite:///")[-1])
    vector_dir = Path(os.getenv("VECTOR_DB_PATH", "vector_store"))

    backup_dir = Path(os.getenv("BACKUP_DIR", "backups"))
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    tar_path = backup_dir / f"backup_{timestamp}.tar.gz"

    with tarfile.open(tar_path, "w:gz") as tar:
        if db_path.exists():
            tar.add(db_path, arcname=db_path.name)
        if vector_dir.exists():
            tar.add(vector_dir, arcname="vector_store")

    logger.info("Backup created at %s", tar_path)

    s3_bucket = os.getenv("BACKUP_S3_BUCKET")
    if upload_to_s3 or s3_bucket:
        if not boto3:
            raise RuntimeError("boto3 not installed for S3 upload")
        bucket = s3_bucket
        key = tar_path.name
        boto3.client("s3").upload_file(str(tar_path), bucket, key)
        logger.info("Uploaded backup to s3://%s/%s", bucket, key)
        return f"s3://{bucket}/{key}"

    return str(tar_path)
