"""Domain value objects for price data: :class:`Candle` and :class:`CandleSeries`.

These are the *domain's* representation of market data — independent of any data
source. The MOEX integration layer maps its transport DTOs onto these
(see ``infrastructure/moex/mapping.py``); the analysis engine consumes only
these domain types, never an infrastructure DTO.

Immutable, framework-light (Pydantic for validation only). Prices use
``Decimal`` and timestamps are timezone-aware UTC, matching the rest of the
domain.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from moex_analyst.domain.market.timeframe import Timeframe

__all__ = ["Candle", "CandleSeries"]


class _FrozenModel(BaseModel):
    """Base for immutable domain value objects."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class Candle(_FrozenModel):
    """A single OHLCV candle.

    ``begin``/``end`` are timezone-aware UTC instants. ``volume`` is in
    securities/lots (0 for indices); ``value`` is turnover in the instrument's
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


class CandleSeries(_FrozenModel):
    """An ordered series of candles for one instrument + timeframe."""

    ticker: str
    timeframe: Timeframe
    candles: tuple[Candle, ...]

    @property
    def is_empty(self) -> bool:
        return len(self.candles) == 0

    @property
    def latest(self) -> Candle | None:
        """Most recent candle, or ``None`` if the series is empty."""
        return self.candles[-1] if self.candles else None
