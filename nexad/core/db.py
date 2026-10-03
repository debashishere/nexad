"""nexad/core/db.py — Async SQLAlchemy engine and session factory.

All repositories import `get_db_session` to obtain a transaction-scoped
async session. The engine is initialised once at module load time using
the DATABASE_URL from application settings.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from nexad.core.config import Settings

# ---------------------------------------------------------------------------
# Engine — created once at module load from environment settings
# ---------------------------------------------------------------------------

_settings = Settings()

engine = create_async_engine(
    _settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False,
)

# ---------------------------------------------------------------------------
# Session factory — expire_on_commit=False is required for async usage so
# that attributes are still accessible after a commit without triggering
# an implicit lazy-load on a closed connection.
# ---------------------------------------------------------------------------

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ---------------------------------------------------------------------------
# Public context-manager — the single import surface for all repositories
# ---------------------------------------------------------------------------


@asynccontextmanager
async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield a transaction-scoped async session.

    Usage::

        async with get_db_session() as session:
            result = await session.execute(select(Organization))

    On any exception the session is rolled back; the session is always
    closed on exit (both happy and error paths).

    Raises:
        Any exception raised inside the ``async with`` block is re-raised
        after rollback so callers can handle or propagate it.
    """
    session: AsyncSession = AsyncSessionLocal()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
