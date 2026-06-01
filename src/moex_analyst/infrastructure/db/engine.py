"""Async SQLAlchemy engine and session-factory construction.

These are pure factories — no module-level engine is created on import, so the
engine lifecycle is owned by the composition root / process lifespan. asyncpg
is the driver (configured via the DSN in :mod:`moex_analyst.core.settings`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

if TYPE_CHECKING:
    from moex_analyst.core.settings import DatabaseSettings

__all__ = ["create_engine", "create_session_factory"]


def create_engine(settings: DatabaseSettings) -> AsyncEngine:
    """Create the async engine with pool settings from configuration.

    ``pool_pre_ping`` validates connections before use, which protects long-
    lived worker processes (bot/scheduler) against stale connections dropped by
    PostgreSQL or an intermediary.
    """
    return create_async_engine(
        settings.async_dsn,
        echo=settings.echo,
        pool_size=settings.pool_size,
        max_overflow=settings.max_overflow,
        pool_timeout=settings.pool_timeout,
        pool_pre_ping=True,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create the session factory bound to ``engine``.

    ``expire_on_commit=False`` keeps attributes accessible after commit (the
    mapper→domain step reads them post-commit); ``autoflush=False`` makes flush
    timing explicit, which is desirable inside a Unit of Work boundary.
    """
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
