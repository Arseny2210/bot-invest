"""Type-safe, environment-based application settings.

A single root :class:`Settings` object aggregates four cohesive sub-settings
(``bot``, ``db``, ``redis``, ``moex``). Values are loaded from environment
variables (and an optional ``.env`` file) using the ``__`` nesting delimiter,
e.g. ``DB__HOST`` populates ``settings.db.host``.

Secrets are typed as :class:`pydantic.SecretStr` so they never leak through
``repr``/logging by accident; :mod:`moex_analyst.core.logging` additionally
scrubs their raw values from log lines.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal
from urllib.parse import quote_plus

from pydantic import BaseModel, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from moex_analyst.core.db_settings import DatabaseSettings

Environment = Literal["local", "dev", "prod", "test"]
LogLevel = Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]

__all__ = [
    "BotSettings",
    "DatabaseSettings",
    "Environment",
    "LogLevel",
    "MoexSettings",
    "RedisSettings",
    "Settings",
    "get_settings",
]


class BotSettings(BaseModel):
    """Telegram bot configuration."""

    token: SecretStr
    use_webhook: bool = False
    webhook_base_url: str | None = None
    webhook_path: str = "/telegram/webhook"
    webhook_secret: SecretStr | None = None
    rate_limit_per_minute: int = Field(default=20, ge=1, le=600)

    @model_validator(mode="after")
    def _check_webhook(self) -> BotSettings:
        if self.use_webhook and (not self.webhook_base_url or self.webhook_secret is None):
            raise ValueError(
                "BOT__WEBHOOK_BASE_URL and BOT__WEBHOOK_SECRET are required "
                "when BOT__USE_WEBHOOK is true",
            )
        return self

    @property
    def webhook_url(self) -> str | None:
        """Full public webhook URL, or ``None`` in polling mode."""
        if not self.use_webhook or not self.webhook_base_url:
            return None
        return f"{self.webhook_base_url.rstrip('/')}{self.webhook_path}"


class RedisSettings(BaseModel):
    """Redis connection configuration. Logical DBs isolate concerns."""

    host: str = "localhost"
    port: int = Field(default=6379, ge=1, le=65535)
    password: SecretStr | None = None
    cache_db: int = Field(default=0, ge=0, le=15)
    fsm_db: int = Field(default=1, ge=0, le=15)

    def _dsn(self, db: int) -> str:
        if self.password is not None:
            auth = f":{quote_plus(self.password.get_secret_value())}@"
        else:
            auth = ""
        return f"redis://{auth}{self.host}:{self.port}/{db}"

    @property
    def cache_dsn(self) -> str:
        """URL for the caching DB (market data, snapshots, ISS responses)."""
        return self._dsn(self.cache_db)

    @property
    def fsm_dsn(self) -> str:
        """URL for the Aiogram FSM-storage DB."""
        return self._dsn(self.fsm_db)


class MoexSettings(BaseModel):
    """MOEX ISS API client configuration."""

    base_url: str = "https://iss.moex.com/iss"
    request_timeout: float = Field(default=10.0, gt=0, le=120)
    connect_timeout: float = Field(default=5.0, gt=0, le=60)
    max_retries: int = Field(default=4, ge=0, le=10)
    backoff_base: float = Field(default=0.5, gt=0, le=10)
    rate_limit_rps: float = Field(default=5.0, gt=0, le=100)
    rate_limit_burst: int = Field(default=10, ge=1, le=100)
    user_agent: str = "moex-ai-analyst/0.1"


class Settings(BaseSettings):
    """Root application settings, assembled from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Environment = "local"
    log_level: LogLevel = "INFO"
    log_serialize: bool = False
    log_diagnose: bool = False

    bot: BotSettings
    db: DatabaseSettings
    redis: RedisSettings
    moex: MoexSettings = Field(default_factory=MoexSettings)

    @property
    def is_production(self) -> bool:
        return self.environment == "prod"

    @model_validator(mode="after")
    def _guard_production(self) -> Settings:
        # Loguru's `diagnose` renders variable values into tracebacks and can
        # expose secrets — forbid it in production regardless of env input.
        if self.is_production and self.log_diagnose:
            raise ValueError("LOG_DIAGNOSE must be false in production")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings singleton.

    Cached so the environment/`.env` is parsed exactly once per process.
    """
    return Settings()
