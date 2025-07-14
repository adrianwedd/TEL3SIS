"""Celery task implementations for background processing."""
from __future__ import annotations

from logging_config import logger
from pathlib import Path

from server.settings import Settings

from datetime import datetime, timedelta, UTC
import tarfile
import time
import shutil
import tempfile
from contextlib import contextmanager

from .recordings import (
    transcribe_recording,
    DEFAULT_OUTPUT_DIR,
    download_recording,
)

import tools.notifications as notifications
from .database import (
    save_call_summary,
    get_session,
    Call,
    set_user_preference,
)
from .self_reflection import generate_self_critique
from tools.language import detect_language
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from .state_manager import StateManager

from .celery_app import celery_app
from prometheus_client import Counter, Histogram

try:  # pragma: no cover - optional dependency
    import boto3
except Exception:  # pragma: no cover - boto3 may not be installed
    boto3 = None

task_invocations = Counter(
    "celery_task_invocations_total",
    "Total times a Celery task was called",
    ["task"],
)
task_failures = Counter(
    "celery_task_failures_total",
    "Total Celery task failures",
    ["task"],
)
task_latency = Histogram(
    "celery_task_latency_seconds",
    "Celery task latency in seconds",
    ["task"],
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60),
)


@contextmanager
def monitor_task(name: str):
    """Context manager to record task metrics."""

    task_invocations.labels(task=name).inc()
    start = time.time()
    try:
        yield
    except Exception:
        task_failures.labels(task=name).inc()
        raise
    finally:
        task_latency.labels(task=name).observe(time.time() - start)


@celery_app.task
def echo(message: str) -> str:
    """Simple debug task that echoes the incoming message."""
    with monitor_task("echo"):
        logger.bind(message=message).info("echo")
        return message


@celery_app.task
def summarize_text(text: str, max_words: int = 30) -> str:
    """Return a naive summary consisting of the first ``max_words``."""
    with monitor_task("summarize_text"):
        words = text.strip().split()
        return " ".join(words[:max_words])


@celery_app.task
def process_recording(
    recording_url: str,
    call_sid: str,
    from_number: str,
    to_number: str,
) -> str:
    """Download a recording and generate a summary."""
    with monitor_task("process_recording"):
        cfg = Settings()
        audio_path = download_recording(
            recording_url,
            auth=(cfg.twilio_account_sid, cfg.twilio_auth_token),
        )
        return transcribe_audio(str(audio_path), call_sid, from_number, to_number)


def transcribe_audio(
    audio_path: str,
    call_sid: str,
    from_number: str,
    to_number: str,
) -> str:
    """Transcribe an audio file and persist a summary."""
    with monitor_task("transcribe_audio"):
        path = transcribe_recording(Path(audio_path))
        logger.bind(audio_path=audio_path).info("transcribed_audio")
        send_transcript_email.delay(str(path))
        text = Path(path).read_text()
        sanitized = notifications.sanitize_transcript(text)
        logger.bind(snippet=sanitized[:100]).debug("transcript_sanitized")
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
        try:
            manager = StateManager()
            manager.set_summary(call_sid, summary, from_number=from_number)
        except Exception:  # noqa: BLE001 - non-critical failure
            pass
        return str(path)


@celery_app.task
def send_transcript_email(transcript_path: str, to_email: str | None = None) -> None:
    """Send the transcript file via email."""
    with monitor_task("send_transcript_email"):
        notifications.send_email(transcript_path, to_email)


@celery_app.task
def cleanup_old_calls(days: int = 30) -> int:
    """Delete call records and files older than ``days`` days."""
    with monitor_task("cleanup_old_calls"):
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
    with monitor_task("backup_data"):
        cfg = Settings()
        db_url = cfg.database_url
        if not db_url.startswith("sqlite:///"):
            raise ValueError("Only SQLite DATABASE_URL supported")
        db_path = Path(db_url.split("sqlite:///")[-1])
        vector_dir = Path(cfg.vector_db_path)

        backup_dir = Path(cfg.backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        tar_path = backup_dir / f"backup_{timestamp}.tar.gz"

        with tarfile.open(tar_path, "w:gz") as tar:
            if db_path.exists():
                tar.add(db_path, arcname=db_path.name)
            if vector_dir.exists():
                tar.add(vector_dir, arcname="vector_store")

        logger.bind(path=tar_path).info("backup_created")

        s3_bucket = cfg.backup_s3_bucket
        if upload_to_s3 or s3_bucket:
            if not boto3:
                raise RuntimeError("boto3 not installed for S3 upload")
            bucket = s3_bucket
            key = tar_path.name
            boto3.client("s3").upload_file(str(tar_path), bucket, key)
            logger.bind(bucket=bucket, key=key).info("backup_uploaded")
            return f"s3://{bucket}/{key}"

        return str(tar_path)


@celery_app.task
def restore_data(archive_path: str) -> bool:
    """Restore the SQLite DB and vector store from ``archive_path``."""
    with monitor_task("restore_data"):
        cfg = Settings()
        db_url = cfg.database_url
        if not db_url.startswith("sqlite:///"):
            raise ValueError("Only SQLite DATABASE_URL supported")
        db_path = Path(db_url.split("sqlite:///")[-1])
        vector_dir = Path(cfg.vector_db_path)

        tar_path = Path(archive_path)
        if str(tar_path).startswith("s3://"):
            if not boto3:
                raise RuntimeError("boto3 not installed for S3 download")
            bucket, key = archive_path[5:].split("/", 1)
            with tempfile.NamedTemporaryFile() as tmp:
                boto3.client("s3").download_file(bucket, key, tmp.name)
                tar_path = Path(tmp.name)

        if not tar_path.exists():
            raise FileNotFoundError(str(tar_path))

        with tempfile.TemporaryDirectory() as tmpdir:
            with tarfile.open(tar_path) as tar:
                tar.extractall(tmpdir)
            extracted_db = Path(tmpdir) / db_path.name
            extracted_vectors = Path(tmpdir) / "vector_store"
            if extracted_db.exists():
                db_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(extracted_db), db_path)
            if extracted_vectors.exists():
                if vector_dir.exists():
                    shutil.rmtree(vector_dir)
                shutil.move(str(extracted_vectors), vector_dir)

        logger.bind(archive=archive_path).info("backup_restored")
        return True


@celery_app.task
def refresh_tokens_task(threshold_seconds: int = 300) -> int:
    """Refresh OAuth tokens nearing expiration."""
    with monitor_task("refresh_tokens_task"):
        cfg = Settings()
        manager = StateManager()
        now = int(datetime.now(UTC).timestamp())
        refreshed = 0
        for user_id, data in manager.iter_tokens():
            expires_at = int(data.get("expires_at", 0)) if data.get("expires_at") else 0
            refresh_token = data.get("refresh_token")
            if not refresh_token or not expires_at:
                continue
            if expires_at - now > threshold_seconds:
                continue
            creds = Credentials(
                data["access_token"],
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=cfg.google_client_id,
                client_secret=cfg.google_client_secret,
            )
            creds.expiry = datetime.fromtimestamp(expires_at, UTC)
            try:
                creds.refresh(Request())
            except Exception as exc:  # pragma: no cover - network errors
                logger.bind(user_id=user_id, error=str(exc)).warning("refresh_failed")
                continue
            new_exp = int(creds.expiry.timestamp()) if creds.expiry else None
            manager.set_token(user_id, creds.token, refresh_token, new_exp)
            refreshed += 1
        return refreshed


@celery_app.task
def reprocess_call(call_id: int) -> bool:
    """Re-run summary and critique generation for a call."""
    with monitor_task("reprocess_call"):
        with get_session() as session:
            call = session.get(Call, call_id)
            if call is None:
                return False
            transcript = Path(call.transcript_path)
            if not transcript.exists():
                return False
            text = transcript.read_text()
            summary = summarize_text(text)
            critique = generate_self_critique(text)
            call.summary = summary
            call.self_critique = critique
            session.commit()
        return True


@celery_app.task
def delete_call_record(call_id: int) -> bool:
    """Delete a call and associated files."""
    with monitor_task("delete_call_record"):
        with get_session() as session:
            call = session.get(Call, call_id)
            if call is None:
                return False
            transcript = Path(call.transcript_path)
            audio = DEFAULT_OUTPUT_DIR / f"{transcript.stem}.mp3"
            transcript.unlink(missing_ok=True)
            audio.unlink(missing_ok=True)
            session.delete(call)
            session.commit()
        return True


@celery_app.task
def clear_cache_task(pattern: str = "cache:*") -> int:
    """Clear cached entries matching ``pattern``."""
    from .cache import clear_cache

    with monitor_task("clear_cache_task"):
        return clear_cache(pattern)
