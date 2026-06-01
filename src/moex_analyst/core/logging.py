"""Loguru-based logging configuration.

Responsibilities:
    * route the stdlib ``logging`` module (uvicorn, SQLAlchemy, aiogram,
      APScheduler) through Loguru via an intercept handler;
    * emit human-readable logs locally and one-JSON-object-per-line in prod;
    * mask secret values so tokens/passwords can never appear in log output,
      even if accidentally interpolated into a message.

Call :func:`configure_logging` exactly once at process startup, before any
other logging happens.
"""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from types import FrameType

    from loguru import Record

    from moex_analyst.core.settings import Settings

__all__ = ["configure_logging"]

_MASK = "***"
# stdlib loggers that should be funnelled through Loguru rather than printing
# on their own handlers.
_INTERCEPTED_LOGGERS = (
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
    "sqlalchemy.engine",
    "aiogram",
    "aiohttp.access",
    "apscheduler",
    "httpx",
    "alembic",
)

_CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "{extra} | <level>{message}</level>"
)


class _InterceptHandler(logging.Handler):
    """Redirect stdlib ``logging`` records into Loguru, preserving call site."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame: FrameType | None = logging.currentframe()
        depth = 2
        while frame is not None and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _collect_secrets(settings: Settings) -> tuple[str, ...]:
    """Return raw secret strings worth masking (len >= 4 to avoid noise)."""
    candidates: list[str | None] = [
        settings.bot.token.get_secret_value(),
        settings.db.password.get_secret_value(),
    ]
    if settings.bot.webhook_secret is not None:
        candidates.append(settings.bot.webhook_secret.get_secret_value())
    if settings.redis.password is not None:
        candidates.append(settings.redis.password.get_secret_value())

    return tuple({s for s in candidates if s and len(s) >= 4})


def _make_mask_patcher(secrets: tuple[str, ...]) -> Any:
    """Build a Loguru patcher that scrubs secret substrings from messages."""

    def patch(record: Record) -> None:
        if not secrets:
            return
        message = record["message"]
        for secret in secrets:
            if secret in message:
                message = message.replace(secret, _MASK)
        record["message"] = message

    return patch


def configure_logging(settings: Settings, *, service: str | None = None) -> None:
    """Configure Loguru and intercept stdlib logging.

    Args:
        settings: the application settings (drives level, json, masking).
        service: optional process tag (``api`` / ``bot`` / ``scheduler``)
            bound into every record's ``extra`` for cross-process filtering.
    """
    logger.remove()
    logger.configure(
        patcher=_make_mask_patcher(_collect_secrets(settings)),
        extra={"service": service or "app"},
    )

    logger.add(
        sys.stderr,
        level=settings.log_level,
        serialize=settings.log_serialize,
        format=_CONSOLE_FORMAT,
        backtrace=False,
        diagnose=settings.log_diagnose,
        enqueue=True,
    )

    # Replace stdlib handlers with the intercept bridge.
    logging.basicConfig(handlers=[_InterceptHandler()], level=logging.NOTSET, force=True)
    for name in _INTERCEPTED_LOGGERS:
        intercepted = logging.getLogger(name)
        intercepted.handlers = [_InterceptHandler()]
        intercepted.propagate = False

    logger.bind(service=service or "app").debug(
        "Logging configured (level={}, serialize={})",
        settings.log_level,
        settings.log_serialize,
    )
