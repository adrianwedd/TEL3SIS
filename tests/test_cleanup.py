from __future__ import annotations

from importlib import reload
from datetime import datetime, timedelta

import server.database as db
import server.tasks as tasks


def test_cleanup_old_calls(monkeypatch, tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    reload(db)
    db.init_db()

    audio_dir = tmp_path / "audio"
    transcript_dir = tmp_path / "transcripts"
    audio_dir.mkdir()
    transcript_dir.mkdir()

    monkeypatch.setattr(tasks, "DEFAULT_OUTPUT_DIR", audio_dir)

    old_transcript = transcript_dir / "old.txt"
    old_audio = audio_dir / "old.mp3"
    old_transcript.write_text("old")
    old_audio.write_text("a")
    old_date = datetime.utcnow() - timedelta(days=31)

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
    new_date = datetime.utcnow() - timedelta(days=5)

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
