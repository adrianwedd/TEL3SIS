from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, JSON, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from werkzeug.security import generate_password_hash
from flask_login import UserMixin

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


class User(Base, UserMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user")


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


def create_user(username: str, password: str, role: str = "user") -> None:
    """Create a new user with hashed password."""
    with get_session() as session:
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=role,
        )
        session.add(user)
        session.commit()


def get_user(user_id: int) -> User | None:
    """Return user by ID."""
    with get_session() as session:
        return session.get(User, user_id)


def get_user_preference(phone_number: str, key: str) -> str | None:
    """Return stored preference value for ``phone_number`` and ``key``."""
    with get_session() as session:
        pref = (
            session.query(UserPreference)
            .filter_by(phone_number=phone_number)
            .one_or_none()
        )
        if pref:
            return pref.data.get(key)
    return None


def set_user_preference(phone_number: str, key: str, value: str) -> None:
    """Persist preference ``key`` for ``phone_number``."""
    with get_session() as session:
        pref = (
            session.query(UserPreference)
            .filter_by(phone_number=phone_number)
            .one_or_none()
        )
        if pref is None:
            pref = UserPreference(phone_number=phone_number, data={key: value})
            session.add(pref)
        else:
            data = dict(pref.data or {})
            data[key] = value
            pref.data = data
        session.commit()
