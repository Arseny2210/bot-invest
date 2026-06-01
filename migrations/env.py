"""Alembic async migration environment.

The database URL is resolved from application settings (single source of truth),
with an optional ``-x dsn=...`` command-line override. Migrations run through an
async engine so the same asyncpg driver is used as the application.

Model metadata is imported from the declarative ``Base``. The models package is
imported for its side effect of registering tables on that metadata; until
models exist (later stage) the metadata is empty and autogenerate is a no-op.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from moex_analyst.core.db_settings import load_database_settings
from moex_analyst.infrastructure.db.base import Base

# Register model tables on Base.metadata once they exist. Kept importable now
# so enabling it later is a one-line change.
# from moex_analyst.infrastructure.db import models  # noqa: F401,ERA001

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    """Resolve the migration DB URL: ``-x dsn=...`` override, else settings."""
    x_args = context.get_x_argument(as_dictionary=True)
    override = x_args.get("dsn")
    if override:
        return override
    return load_database_settings().async_dsn


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL, no DB connection)."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode via an async engine."""
    engine = create_async_engine(_database_url(), poolclass=pool.NullPool)
    try:
        async with engine.connect() as connection:
            await connection.run_sync(_do_run_migrations)
    finally:
        await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
