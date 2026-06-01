"""Application-level exception types.

Use cases translate infrastructure exceptions into these types so the
presentation layer never needs to import from infrastructure.
"""

from __future__ import annotations

__all__ = [
    "ApplicationError",
    "DataSourceError",
    "EmptyDataError",
    "InstrumentNotFoundError",
    "RateLimitError",
    "TickerNotFoundError",
]


class ApplicationError(Exception):
    """Base for all application-level errors."""


class TickerNotFoundError(ApplicationError):
    """Ticker is not in the tracked instruments registry."""


class MarketDataError(ApplicationError):
    """Base for MOEX data access errors."""


class InstrumentNotFoundError(MarketDataError):
    """MOEX returned 404 for the instrument."""


class EmptyDataError(MarketDataError):
    """MOEX returned an empty dataset."""


class RateLimitError(MarketDataError):
    """MOEX rate-limited the request."""


class DataSourceError(MarketDataError):
    """Generic MOEX data source error."""
