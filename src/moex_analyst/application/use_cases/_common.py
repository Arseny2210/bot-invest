"""Shared helpers for the application use cases.

Pure, dependency-light utilities: how much candle history to request per
timeframe, the bullishness ranking score, and the tracked-instrument list.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from moex_analyst.domain.market.timeframe import Timeframe
from moex_analyst.infrastructure.moex import INSTRUMENT_REGISTRY

if TYPE_CHECKING:
    from datetime import date

    from moex_analyst.domain.analysis import AnalysisResult

__all__ = ["lookback_date_from", "score_bullishness", "tracked_tickers"]

# Calendar-day lookback per timeframe — generous enough that, after weekends/
# holidays, enough bars remain for the engine's EMA50 warm-up (~50 bars).
_LOOKBACK_DAYS: dict[Timeframe, int] = {
    Timeframe.H1: 30,
    Timeframe.H4: 120,
    Timeframe.D1: 400,
}


def lookback_date_from(timeframe: Timeframe, *, now: datetime | None = None) -> date:
    """Earliest calendar date to request so the engine has enough history."""
    reference = now or datetime.now(UTC)
    return (reference - timedelta(days=_LOOKBACK_DAYS[timeframe])).date()


def score_bullishness(analysis: AnalysisResult) -> float:
    """Net directional bias in [-1, 1] used to rank instruments.

    Bullish probability minus bearish probability: positive ranks higher
    (more bullish), negative lower (more bearish). Deterministic and pure.
    """
    probs = analysis.probabilities
    return probs.bullish - probs.bearish


def tracked_tickers() -> tuple[str, ...]:
    """The fixed set of platform-tracked tickers, in registry order."""
    return tuple(INSTRUMENT_REGISTRY)
