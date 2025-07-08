from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, JSON, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///tel3sis.db")

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, future=True)


class Base(DeclarativeBase):
    pass


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True)
    call_sid = Column(String, unique=True, nullable=False)
    from_number = Column(String, nullable=False)
    to_number = Column(String, nullable=False)
    transcript_path = Column(String, nullable=False)
    summary = Column(String, nullable=False)
    self_critique = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    phone_number = Column(String, unique=True, nullable=False)
    data = Column(JSON, default=dict)


def init_db() -> None:
    """Create database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    """Return a new database session."""
    return SessionLocal()


def save_call_summary(
    call_sid: str,
    from_number: str,
    to_number: str,
    transcript_path: str,
    summary: str,
    self_critique: str | None = None,
) -> None:
    """Persist a completed call with summary to the database."""
    with get_session() as session:
        call = Call(
            call_sid=call_sid,
            from_number=from_number,
            to_number=to_number,
            transcript_path=transcript_path,
            summary=summary,
            self_critique=self_critique,
        )
        session.add(call)
        session.commit()
