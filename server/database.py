"""Database models and helpers using SQLAlchemy."""
from __future__ import annotations

from datetime import datetime, UTC

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    JSON,
    String,
    Index,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Any
import asyncio
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

from .settings import Settings

engine = None
AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


def _ensure_engine() -> None:
    """Initialize the SQLAlchemy engine and session maker."""
    global engine, AsyncSessionLocal
    if engine is None:
        cfg = Settings()
        db_url = cfg.database_url
        if db_url.startswith("sqlite:///"):
            db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
        elif db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
        engine = create_async_engine(db_url, future=True)
        AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Call(Base):
    __tablename__ = "calls"
    __table_args__ = (
        Index("ix_calls_created_at", "created_at"),
        Index("ix_calls_from_number", "from_number"),
    )

    id = Column(Integer, primary_key=True)
    call_sid = Column(String, unique=True, nullable=False)
    from_number = Column(String, nullable=False)
    to_number = Column(String, nullable=False)
    transcript_path = Column(String, nullable=False)
    summary = Column(String, nullable=False)
    self_critique = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    phone_number = Column(String, unique=True, nullable=False)
    data = Column(JSON, default=dict)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user")


class APIKey(Base):
    """API key hashed with owner."""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    owner = Column(String, nullable=False)
    key_hash = Column(String, nullable=False, unique=True)


async def init_db_async() -> None:
    """Create database tables if they do not exist."""
    _ensure_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def init_db() -> None:
    """Synchronous wrapper for ``init_db_async``."""
    asyncio.run(init_db_async())


@asynccontextmanager
async def get_session_async() -> AsyncGenerator[AsyncSession, None]:
    """Return a new async database session."""
    _ensure_engine()
    assert AsyncSessionLocal is not None
    async with AsyncSessionLocal() as session:
        yield session


@contextmanager
def get_session() -> Any:
    """Synchronous wrapper for ``get_session_async``."""
    ctx = get_session_async()
    session = asyncio.run(ctx.__aenter__())
    try:
        yield session
    finally:
        asyncio.run(ctx.__aexit__(None, None, None))


async def save_call_summary_async(
    call_sid: str,
    from_number: str,
    to_number: str,
    transcript_path: str,
    summary: str,
    self_critique: str | None = None,
) -> None:
    """Persist a completed call with summary to the database."""
    async with get_session_async() as session:
        call = Call(
            call_sid=call_sid,
            from_number=from_number,
            to_number=to_number,
            transcript_path=transcript_path,
            summary=summary,
            self_critique=self_critique,
        )
        session.add(call)
        await session.commit()


def save_call_summary(*args: Any, **kwargs: Any) -> None:
    """Synchronous wrapper for ``save_call_summary_async``."""
    asyncio.run(save_call_summary_async(*args, **kwargs))


async def create_user_async(username: str, password: str, role: str = "user") -> None:
    """Create a new user with hashed password."""
    async with get_session_async() as session:
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=role,
        )
        session.add(user)
        await session.commit()


def create_user(*args: Any, **kwargs: Any) -> None:
    asyncio.run(create_user_async(*args, **kwargs))


async def get_user_async(user_id: int) -> User | None:
    """Return user by ID."""
    async with get_session_async() as session:
        return await session.get(User, user_id)


def get_user(*args: Any, **kwargs: Any) -> User | None:
    return asyncio.run(get_user_async(*args, **kwargs))


async def get_user_preference_async(phone_number: str, key: str) -> str | None:
    """Return stored preference value for ``phone_number`` and ``key``."""
    async with get_session_async() as session:
        result = await session.execute(
            select(UserPreference).filter_by(phone_number=phone_number)
        )
        pref = result.scalar_one_or_none()
        if pref:
            return pref.data.get(key)
    return None


def get_user_preference(*args: Any, **kwargs: Any) -> str | None:
    return asyncio.run(get_user_preference_async(*args, **kwargs))


async def set_user_preference_async(phone_number: str, key: str, value: str) -> None:
    """Persist preference ``key`` for ``phone_number``."""
    async with get_session_async() as session:
        result = await session.execute(
            select(UserPreference).filter_by(phone_number=phone_number)
        )
        pref = result.scalar_one_or_none()
        if pref is None:
            pref = UserPreference(phone_number=phone_number, data={key: value})
            session.add(pref)
        else:
            data = dict(pref.data or {})
            data[key] = value
            pref.data = data
        await session.commit()


def set_user_preference(*args: Any, **kwargs: Any) -> None:
    asyncio.run(set_user_preference_async(*args, **kwargs))


async def create_api_key_async(owner: str) -> str:
    """Generate an API key for ``owner`` and store the hashed value."""
    key = secrets.token_urlsafe(32)
    key_hash = generate_password_hash(key)
    async with get_session_async() as session:
        session.add(APIKey(owner=owner, key_hash=key_hash))
        await session.commit()
    return key


def create_api_key(*args: Any, **kwargs: Any) -> str:
    return asyncio.run(create_api_key_async(*args, **kwargs))


async def verify_api_key_async(key: str) -> bool:
    """Return True if ``key`` is valid."""
    async with get_session_async() as session:
        result = await session.execute(select(APIKey))
        for api_key in result.scalars().all():
            if check_password_hash(api_key.key_hash, key):
                return True
    return False


def verify_api_key(*args: Any, **kwargs: Any) -> bool:
    return asyncio.run(verify_api_key_async(*args, **kwargs))


async def delete_user_async(username: str) -> bool:
    """Delete the user with ``username`` if it exists."""
    async with get_session_async() as session:
        result = await session.execute(select(User).filter_by(username=username))
        user = result.scalar_one_or_none()
        if user is None:
            return False
        await session.delete(user)
        await session.commit()
        return True


def delete_user(*args: Any, **kwargs: Any) -> bool:
    return asyncio.run(delete_user_async(*args, **kwargs))


async def list_users_async() -> list[User]:
    """Return all users sorted by username."""
    async with get_session_async() as session:
        result = await session.execute(select(User).order_by(User.username))
        return list(result.scalars().all())


def list_users() -> list[User]:
    return asyncio.run(list_users_async())


async def update_user_async(
    username: str, password: str | None = None, role: str | None = None
) -> bool:
    """Update user credentials and/or role. Return False if not found."""
    async with get_session_async() as session:
        result = await session.execute(select(User).filter_by(username=username))
        user = result.scalar_one_or_none()
        if user is None:
            return False
        if password is not None:
            user.password_hash = generate_password_hash(password)
        if role is not None:
            user.role = role
        await session.commit()
        return True


def update_user(*args: Any, **kwargs: Any) -> bool:
    return asyncio.run(update_user_async(*args, **kwargs))


async def get_agent_config_async() -> dict:
    """Return global agent configuration."""
    async with get_session_async() as session:
        result = await session.execute(
            select(UserPreference).filter_by(phone_number="__agent__")
        )
        pref = result.scalar_one_or_none()
        return dict(pref.data) if pref else {}


def get_agent_config() -> dict:
    return asyncio.run(get_agent_config_async())


async def update_agent_config_async(**settings: str) -> None:
    """Update global agent configuration in the database."""
    if not settings:
        return
    async with get_session_async() as session:
        result = await session.execute(
            select(UserPreference).filter_by(phone_number="__agent__")
        )
        pref = result.scalar_one_or_none()
        if pref is None:
            pref = UserPreference(phone_number="__agent__", data=settings)
            session.add(pref)
        else:
            data = dict(pref.data or {})
            data.update(settings)
            pref.data = data
        await session.commit()


def update_agent_config(*args: Any, **kwargs: Any) -> None:
    asyncio.run(update_agent_config_async(*args, **kwargs))
