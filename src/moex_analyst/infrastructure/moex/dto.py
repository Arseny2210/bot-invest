"""Typed DTOs — the output contract of the MOEX integration layer.

These are immutable Pydantic models. Prices and turnover use ``Decimal`` (never
float) and all timestamps are timezone-aware UTC. The ISS API returns naive
Moscow-time strings; the mappers convert them on the way in, so nothing outside
this layer ever sees a naive datetime or an ISS-shaped row.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from moex_analyst.domain.market.timeframe import Timeframe
from moex_analyst.infrastructure.moex.config import MarketType

__all__ = ["CandleDTO", "CandleSeriesDTO", "InstrumentDTO", "QuoteDTO"]


class _FrozenModel(BaseModel):
    """Base for immutable DTOs."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class InstrumentDTO(_FrozenModel):
    """Static metadata for one tracked instrument."""

    ticker: str
    secid: str
    shortname: str
    market_type: MarketType
    board: str
    currency: str = "RUB"
    lot_size: int = 1
    decimals: int = 2


class CandleDTO(_FrozenModel):
    """A single OHLCV candle.

    ``begin``/``end`` are timezone-aware UTC instants. ``volume`` is in lots/
    securities (0 for indices); ``value`` is turnover in the instrument's
    currency.
    """

    begin: datetime
    end: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int = Field(ge=0)
    value: Decimal = Field(ge=0)


class CandleSeriesDTO(_FrozenModel):
    """An ordered series of candles for one instrument + timeframe."""

    ticker: str
    timeframe: Timeframe
    candles: tuple[CandleDTO, ...]

    @property
    def is_empty(self) -> bool:
        return len(self.candles) == 0

    @property
    def latest(self) -> CandleDTO | None:
        """Most recent candle, or ``None`` if the series is empty."""
        return self.candles[-1] if self.candles else None


class QuoteDTO(_FrozenModel):
    """Current marketdata snapshot for one instrument.

    Every price field is optional: ISS omits/nulls them outside trading hours
    or for instruments without an order book (indices have no ``bid``/``offer``).
    """

    secid: str
    board: str
    last: Decimal | None = None
    bid: Decimal | None = None
    offer: Decimal | None = None
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    value_today: Decimal | None = Field(default=None, ge=0)
    volume_today: int | None = Field(default=None, ge=0)
    num_trades: int | None = Field(default=None, ge=0)
    updated_at: datetime | None = None
