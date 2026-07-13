"""
SQLAlchemy async engine + session factory + base declarative model.

Supports both PostgreSQL (production) and SQLite (development) via DATABASE_URL.
"""
from __future__ import annotations
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

from app.core.config import settings


# ── Engine Configuration ──────────────────────────────────────────────────────

_engine_kwargs: dict = {
    "echo": settings.DEBUG,
    "pool_pre_ping": True,
    "future": True,
}

# SQLite doesn't support pool_size / max_overflow
if "sqlite" not in settings.DATABASE_URL:
    _engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 10,
    })

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    """All ORM models inherit from this base."""
    pass


# ── Dependency ────────────────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Startup: create tables ────────────────────────────────────────────────────

async def create_all_tables() -> None:
    """Called on app startup. For production use Alembic migrations instead."""
    async with engine.begin() as conn:
        from app.database import models as _  # noqa: ensure models are imported
        await conn.run_sync(Base.metadata.create_all)