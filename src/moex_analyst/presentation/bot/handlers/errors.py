"""Translation of domain/infrastructure errors into user-facing messages.

Handlers call :func:`friendly_error` to turn an exception into a polite,
actionable Telegram message. Keeps error wording in one place and out of the
individual handlers.
"""

from __future__ import annotations

from moex_analyst.application.exceptions import (
    DataSourceError,
    EmptyDataError,
    InstrumentNotFoundError,
    RateLimitError,
    TickerNotFoundError,
)
from moex_analyst.domain.analysis import InsufficientDataError
from moex_analyst.presentation.bot.formatters import format_error

__all__ = ["friendly_error"]


def friendly_error(exc: Exception) -> str:
    """Map an exception to a user-facing HTML message."""
    if isinstance(exc, TickerNotFoundError):
        return format_error("Тикер не найден. Выберите инструмент через меню.")
    # First matching (type -> message) pair wins; order matters (subclasses
    # before their base, e.g. InstrumentNotFoundError before DataSourceError).
    for exc_type, message in _MESSAGES:
        if isinstance(exc, exc_type):
            return format_error(message)
    return format_error("Что-то пошло не так при обработке запроса.")


_MESSAGES: tuple[tuple[type[Exception], str], ...] = (
    (InsufficientDataError, "Недостаточно истории цен для анализа этого инструмента."),
    (InstrumentNotFoundError, "У MOEX нет данных по этому инструменту."),
    (EmptyDataError, "MOEX не вернул данных (возможно, рынок закрыт)."),
    (RateLimitError, "MOEX ограничивает запросы — повторите попытку позже."),
    (DataSourceError, "Не удалось подключиться к MOEX. Повторите попытку."),
)
