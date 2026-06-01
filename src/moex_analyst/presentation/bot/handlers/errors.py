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
from moex_analyst.application.use_cases._common import tracked_tickers
from moex_analyst.domain.analysis import InsufficientDataError
from moex_analyst.presentation.bot.formatters import format_error

__all__ = ["friendly_error"]


def friendly_error(exc: Exception) -> str:
    """Map an exception to a user-facing HTML message."""
    if isinstance(exc, TickerNotFoundError):
        tracked = ", ".join(tracked_tickers())
        return format_error(f"Unknown ticker. Tracked instruments: {tracked}.")
    # First matching (type -> message) pair wins; order matters (subclasses
    # before their base, e.g. InstrumentNotFoundError before DataSourceError).
    for exc_type, message in _MESSAGES:
        if isinstance(exc, exc_type):
            return format_error(message)
    return format_error("Something went wrong handling that request.")


_MESSAGES: tuple[tuple[type[Exception], str], ...] = (
    (InsufficientDataError, "Not enough price history to analyse this instrument yet."),
    (InstrumentNotFoundError, "MOEX has no data for this instrument right now."),
    (EmptyDataError, "MOEX returned no data (the market may be closed)."),
    (RateLimitError, "MOEX is rate-limiting requests — please try again shortly."),
    (DataSourceError, "Couldn't reach MOEX. Please try again in a moment."),
)
