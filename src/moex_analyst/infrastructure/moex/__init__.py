"""MOEX ISS integration — data acquisition layer.

Public surface: the three services (instruments, candles, quotes), the HTTP
client they share, the typed DTOs they return, the timeframe/instrument
configuration, and the error hierarchy.
"""

from moex_analyst.infrastructure.moex.config import (
    INSTRUMENT_REGISTRY,
    InstrumentRef,
    MarketType,
    Timeframe,
    resolve_instrument,
)
from moex_analyst.infrastructure.moex.dto import (
    CandleDTO,
    CandleSeriesDTO,
    InstrumentDTO,
    QuoteDTO,
)
from moex_analyst.infrastructure.moex.errors import (
    MoexClientError,
    MoexEmptyDataError,
    MoexError,
    MoexNotFoundError,
    MoexRateLimitedError,
    MoexResponseError,
    MoexServerError,
    MoexTimeoutError,
    MoexTransportError,
)
from moex_analyst.infrastructure.moex.services.candles import CandleService
from moex_analyst.infrastructure.moex.services.instruments import InstrumentService
from moex_analyst.infrastructure.moex.services.quotes import QuoteService
from moex_analyst.infrastructure.moex.transport.client import MoexHttpClient

__all__ = [
    "INSTRUMENT_REGISTRY",
    "CandleDTO",
    "CandleSeriesDTO",
    "CandleService",
    "InstrumentDTO",
    "InstrumentRef",
    "InstrumentService",
    "MarketType",
    "MoexClientError",
    "MoexEmptyDataError",
    "MoexError",
    "MoexHttpClient",
    "MoexNotFoundError",
    "MoexRateLimitedError",
    "MoexResponseError",
    "MoexServerError",
    "MoexTimeoutError",
    "MoexTransportError",
    "QuoteDTO",
    "QuoteService",
    "Timeframe",
    "resolve_instrument",
]
