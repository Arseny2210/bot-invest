"""Shared fixtures and builders for analysis unit tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from moex_analyst.domain.market.candle import Candle, CandleSeries
from moex_analyst.domain.market.timeframe import Timeframe

_BASE = datetime(2024, 1, 1, tzinfo=UTC)


def make_candle(
    i: int,
    *,
    open_: float,
    high: float,
    low: float,
    close: float,
    volume: int = 1000,
) -> Candle:
    """Build a single domain candle at hour offset ``i`` from a fixed base time."""
    begin = _BASE + timedelta(hours=i)
    return Candle(
        begin=begin,
        end=begin + timedelta(hours=1),
        open=Decimal(str(open_)),
        high=Decimal(str(high)),
        low=Decimal(str(low)),
        close=Decimal(str(close)),
        volume=volume,
        value=Decimal(str(close * volume)),
    )


def series_from_closes(
    closes: list[float],
    *,
    ticker: str = "TEST",
    timeframe: Timeframe = Timeframe.H1,
    spread: float = 1.0,
    volume: int = 1000,
) -> CandleSeries:
    """Build a domain series where each bar's high/low straddle the close."""
    candles = tuple(
        make_candle(
            i,
            open_=closes[i - 1] if i > 0 else closes[0],
            high=c + spread,
            low=c - spread,
            close=c,
            volume=volume,
        )
        for i, c in enumerate(closes)
    )
    return CandleSeries(ticker=ticker, timeframe=timeframe, candles=candles)


@pytest.fixture
def uptrend_closes() -> list[float]:
    """Monotonically rising closes."""
    return [100.0 + i for i in range(60)]


@pytest.fixture
def downtrend_closes() -> list[float]:
    """Monotonically falling closes."""
    return [160.0 - i for i in range(60)]


@pytest.fixture
def flat_closes() -> list[float]:
    """Constant closes (zero volatility)."""
    return [100.0] * 60
