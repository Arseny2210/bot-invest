"""Database settings and a standalone, DB-only environment loader.

This module is intentionally self-contained: it imports nothing from the bot,
redis, or root :class:`~moex_analyst.core.settings.Settings`. It exists so that
tooling which needs *only* the database configuration — chiefly Alembic — can
load it from ``DB__*`` environment variables without triggering validation of
unrelated subsystems (e.g. requiring ``BOT__TOKEN``).

``DatabaseSettings`` remains a plain :class:`~pydantic.BaseModel` so that the
root settings object can keep nesting it exactly as before (unchanged runtime
behavior). The standalone loader is a thin :class:`~pydantic_settings.BaseSettings`
subclass that reuses those same fields via inheritance — single source of truth.
"""

from __future__ import annotations

from urllib.parse import quote_plus

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["DatabaseSettings", "load_database_settings"]


class DatabaseSettings(BaseModel):
    """PostgreSQL connection and pool configuration."""

    host: str = "localhost"
    port: int = Field(default=5432, ge=1, le=65535)
    user: str = "moex"
    password: SecretStr
    name: str = "moex_analyst"
    pool_size: int = Field(default=10, ge=1, le=100)
    max_overflow: int = Field(default=5, ge=0, le=100)
    pool_timeout: int = Field(default=30, ge=1, le=300)
    echo: bool = False

    def _dsn(self, driver: str) -> str:
        password = quote_plus(self.password.get_secret_value())
        user = quote_plus(self.user)
        return f"postgresql+{driver}://{user}:{password}@{self.host}:{self.port}/{self.name}"

    @property
    def async_dsn(self) -> str:
        """SQLAlchemy async URL (asyncpg) for the application engine."""
        return self._dsn("asyncpg")

    @property
    def sync_dsn(self) -> str:
        """SQLAlchemy URL with the async driver, used by Alembic's async env."""
        # Alembic runs migrations through an async engine (see migrations/env.py),
        # so the same asyncpg driver is reused — no separate sync driver needed.
        return self._dsn("asyncpg")


class _DatabaseEnvSettings(DatabaseSettings, BaseSettings):
    """Loads :class:`DatabaseSettings` fields directly from ``DB__*`` env vars.

    Reuses the field definitions from ``DatabaseSettings`` (no duplication) and
    adds only the settings-source machinery. The ``DB__`` prefix maps to the
    very same variables the root settings read via its nested delimiter
    (``DB__HOST`` → ``host``, ``DB__PASSWORD`` → ``password``, ...), so values
    are identical regardless of which loader is used.
    """

    model_config = SettingsConfigDict(
        env_prefix="DB__",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


def load_database_settings() -> DatabaseSettings:
    """Return :class:`DatabaseSettings` built from ``DB__*`` env vars only.

    Does not import or validate bot/redis configuration. Used by Alembic so
    migrations depend on the database settings alone.
    """
    return _DatabaseEnvSettings()
