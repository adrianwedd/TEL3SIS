from __future__ import annotations

from importlib import reload
from datetime import datetime, timedelta, UTC
from pathlib import Path
import tarfile

import pytest
from celery.contrib.testing.worker import start_worker


@pytest.fixture
def celery_setup(monkeypatch, tmp_path):
    """Configure Celery and database for tests."""
    monkeypatch.setenv("CELERY_BROKER_URL", "memory://")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "cache+memory://")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    vector_dir = tmp_path / "vectors"
    monkeypatch.setenv("VECTOR_DB_PATH", str(vector_dir))
    vector_dir.mkdir()

    import server.celery_app as celery_app
    import server.database as db
    import server.tasks as tasks

    reload(celery_app)
    celery_app.celery_app.conf.task_default_queue = "default"
    reload(db)
    db.init_db()
    reload(tasks)
    return celery_app.celery_app, tasks, db


@pytest.fixture
def celery_worker(celery_setup):
    app, tasks, db = celery_setup
    with start_worker(app, queues=["default"], perform_ping_check=False):
        yield tasks, db


def test_send_transcript_email(celery_worker, monkeypatch, tmp_path):
    tasks, _ = celery_worker
    transcript = tmp_path / "t.txt"
    transcript.write_text("hello")
    sent: dict[str, str | None] = {}

    monkeypatch.setattr(
        "tools.notifications.send_email",
        lambda path, to=None: sent.update({"path": path, "to": to}),
    )

    result = tasks.send_transcript_email.delay(str(transcript), "user@test")
    result.get(timeout=5)
    assert sent == {"path": str(transcript), "to": "user@test"}


def test_transcribe_audio(celery_worker, monkeypatch, tmp_path):
    tasks, _ = celery_worker
    transcript = tmp_path / "trans.txt"
    transcript.write_text("hola mundo")

    monkeypatch.setattr(tasks, "transcribe_recording", lambda *_: transcript)
    monkeypatch.setattr(tasks, "generate_self_critique", lambda *_: "crit")
    monkeypatch.setattr(tasks, "summarize_text", lambda *_: "summary")
    monkeypatch.setattr(tasks, "detect_language", lambda *_: "es")

    prefs: dict[tuple[str, str], str] = {}
    monkeypatch.setattr(
        tasks,
        "set_user_preference",
        lambda num, key, val: prefs.setdefault((num, key), val),
    )

    saved: list[tuple] = []
    monkeypatch.setattr(tasks, "save_call_summary", lambda *args: saved.append(args))

    sent: dict[str, str | None] = {}
    monkeypatch.setattr(
        "tools.notifications.send_email",
        lambda path, to=None: sent.update({"path": path, "to": to}),
    )

    results = []
    orig_delay = tasks.send_transcript_email.delay

    def capture_delay(*args, **kwargs):
        r = orig_delay(*args, **kwargs)
        results.append(r)
        return r

    monkeypatch.setattr(tasks.send_transcript_email, "delay", capture_delay)

    path = tasks.transcribe_audio("audio.wav", "CA1", "+100", "+200")
    results[0].get(timeout=5)

    assert path == str(transcript)
    assert prefs[("+100", "language")] == "es"
    assert sent["path"] == str(transcript)
    assert saved[0][0] == "CA1"


def test_cleanup_old_calls(celery_worker, monkeypatch, tmp_path):
    tasks, db = celery_worker
    audio_dir = tmp_path / "audio"
    transcript_dir = tmp_path / "transcripts"
    audio_dir.mkdir()
    transcript_dir.mkdir()

    monkeypatch.setattr(tasks, "DEFAULT_OUTPUT_DIR", audio_dir)

    old_transcript = transcript_dir / "old.txt"
    old_audio = audio_dir / "old.mp3"
    old_transcript.write_text("old")
    old_audio.write_text("a")
    old_date = datetime.now(UTC) - timedelta(days=40)

    with db.get_session() as session:
        session.add(
            db.Call(
                call_sid="old",
                from_number="111",
                to_number="222",
                transcript_path=str(old_transcript),
                summary="s",
                self_critique=None,
                created_at=old_date,
            )
        )
        session.commit()

    new_transcript = transcript_dir / "new.txt"
    new_audio = audio_dir / "new.mp3"
    new_transcript.write_text("new")
    new_audio.write_text("a")
    new_date = datetime.now(UTC) - timedelta(days=5)

    with db.get_session() as session:
        session.add(
            db.Call(
                call_sid="new",
                from_number="111",
                to_number="222",
                transcript_path=str(new_transcript),
                summary="s",
                self_critique=None,
                created_at=new_date,
            )
        )
        session.commit()

    result = tasks.cleanup_old_calls.delay(days=30)
    removed = result.get(timeout=5)

    assert removed == 1
    assert not old_transcript.exists()
    assert not old_audio.exists()
    assert new_transcript.exists()
    assert new_audio.exists()
    with db.get_session() as session:
        calls = session.query(db.Call).all()
        assert len(calls) == 1
        assert calls[0].call_sid == "new"


def test_backup_data(celery_worker, tmp_path):
    tasks, _ = celery_worker

    result = tasks.backup_data.delay()
    path = result.get(timeout=5)
    assert path.endswith(".tar.gz")
    assert Path(path).exists()
    with tarfile.open(path) as tar:
        names = tar.getnames()
    assert "test.db" in names
    assert "vector_store" in names
