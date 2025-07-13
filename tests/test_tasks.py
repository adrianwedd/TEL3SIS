from __future__ import annotations

from datetime import datetime, timedelta, UTC
from pathlib import Path
import shutil
import tarfile


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


def test_transcribe_audio(monkeypatch, tmp_path):
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    vector_dir = tmp_path / "vectors"
    monkeypatch.setenv("VECTOR_DB_PATH", str(vector_dir))
    vector_dir.mkdir()
    from importlib import reload
    from tests.db_utils import migrate_sqlite

    import server.celery_app as celery_app
    import server.tasks as tasks

    migrate_sqlite(monkeypatch, tmp_path)
    reload(celery_app)
    celery_app.celery_app.conf.task_default_queue = "default"
    from prometheus_client import REGISTRY

    for collector in [
        getattr(tasks, "task_invocations", None),
        getattr(tasks, "task_failures", None),
        getattr(tasks, "task_latency", None),
    ]:
        if collector is not None:
            try:
                REGISTRY.unregister(collector)
            except KeyError:
                pass
    tasks = reload(tasks)
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

    class DummyResult:
        def get(self, timeout: float | None = None) -> None:  # noqa: D401
            return None

    def capture_delay(path: str, to: str | None = None):
        tasks.send_transcript_email.run(path, to_email=to)
        results.append((path, to))
        return DummyResult()

    monkeypatch.setattr(tasks.send_transcript_email, "delay", capture_delay)

    summaries: list[tuple[str, str, str]] = []

    class DummyManager:
        def set_summary(
            self, cid: str, text: str, from_number: str | None = None
        ) -> None:  # noqa: D401
            summaries.append((cid, text, from_number))

    monkeypatch.setattr(tasks, "StateManager", DummyManager)

    path = tasks.transcribe_audio("audio.wav", "CA1", "+100", "+200")

    assert path == str(transcript)
    assert prefs[("+100", "language")] == "es"
    assert sent["path"] == str(transcript)
    assert saved[0][0] == "CA1"
    assert summaries[0] == ("CA1", "summary", "+100")


def test_process_recording(monkeypatch, tmp_path):
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("BASE_URL", "http://localhost")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    vector_dir = tmp_path / "vectors"
    monkeypatch.setenv("VECTOR_DB_PATH", str(vector_dir))
    vector_dir.mkdir()
    from importlib import reload
    from tests.db_utils import migrate_sqlite

    import server.celery_app as celery_app
    import server.tasks as tasks

    migrate_sqlite(monkeypatch, tmp_path)
    reload(celery_app)
    celery_app.celery_app.conf.task_default_queue = "default"
    from prometheus_client import REGISTRY

    for collector in [
        getattr(tasks, "task_invocations", None),
        getattr(tasks, "task_failures", None),
        getattr(tasks, "task_latency", None),
    ]:
        if collector is not None:
            try:
                REGISTRY.unregister(collector)
            except KeyError:
                pass
    tasks = reload(tasks)

    audio_file = tmp_path / "audio" / "a.mp3"
    audio_file.parent.mkdir()

    monkeypatch.setattr(
        tasks,
        "download_recording",
        lambda url, *, output_dir=tmp_path / "audio", auth=None: audio_file,
    )

    called: dict[str, tuple] = {}

    def fake_transcribe(path: str, cid: str, f: str, t: str) -> str:
        called["args"] = (path, cid, f, t)
        return "ok"

    monkeypatch.setattr(tasks, "transcribe_audio", fake_transcribe)

    result = tasks.process_recording("http://x", "CA1", "+1", "+2")

    assert result == "ok"
    assert called["args"] == (str(audio_file), "CA1", "+1", "+2")


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


def test_restore_data(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    vector_dir = tmp_path / "vectors"
    monkeypatch.setenv("VECTOR_DB_PATH", str(vector_dir))
    vector_dir.mkdir()
    from importlib import reload
    from tests.db_utils import migrate_sqlite

    import server.tasks as tasks

    migrate_sqlite(monkeypatch, tmp_path)
    from prometheus_client import REGISTRY

    for collector in [
        getattr(tasks, "task_invocations", None),
        getattr(tasks, "task_failures", None),
        getattr(tasks, "task_latency", None),
    ]:
        if collector is not None:
            try:
                REGISTRY.unregister(collector)
            except KeyError:
                pass
    tasks = reload(tasks)

    path = tasks.backup_data.run()

    (tmp_path / "test.db").unlink()
    shutil.rmtree(vector_dir)

    result = tasks.restore_data.run(path)
    assert result is True
    assert (tmp_path / "test.db").exists()
    assert vector_dir.exists()
