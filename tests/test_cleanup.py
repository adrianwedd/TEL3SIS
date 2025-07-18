from __future__ import annotations

from datetime import datetime, timedelta, UTC

from importlib import reload
from .db_utils import migrate_sqlite
import server.tasks as tasks


def test_cleanup_old_calls(monkeypatch, tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    db = migrate_sqlite(monkeypatch, tmp_path)

    audio_dir = tmp_path / "audio"
    transcript_dir = tmp_path / "transcripts"
    audio_dir.mkdir()
    transcript_dir.mkdir()

    monkeypatch.setattr(tasks, "DEFAULT_OUTPUT_DIR", audio_dir)

    old_transcript = transcript_dir / "old.txt"
    old_audio = audio_dir / "old.mp3"
    old_transcript.write_text("old")
    old_audio.write_text("a")
    old_date = datetime.now(UTC) - timedelta(days=31)

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
    from prometheus_client import REGISTRY

    # Remove previously registered metrics to avoid duplicate errors when
    # reloading the tasks module during tests.
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

    reload(tasks)
    monkeypatch.setattr(tasks, "DEFAULT_OUTPUT_DIR", audio_dir)

    removed = tasks.cleanup_old_calls.run(days=30)
    assert removed == 1
    assert not old_transcript.exists()
    assert not old_audio.exists()
    assert new_transcript.exists()
    assert new_audio.exists()
    with db.get_session() as session:
        calls = session.query(db.Call).all()
        assert len(calls) == 1
        assert calls[0].call_sid == "new"
