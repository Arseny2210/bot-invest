"""Application-layer DTOs returned by the use cases.

These bundle the outputs of the existing domain/infrastructure services (MOEX
DTOs, :class:`AnalysisResult`, :class:`Alert`) into the shapes the presentation
layer consumes. They are immutable, behaviour-light value objects — the
presentation layer formats them, it never reaches past them into a service.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from moex_analyst.domain.alerts import Alert
    from moex_analyst.domain.analysis import AnalysisResult
    from moex_analyst.domain.market.timeframe import Timeframe
    from moex_analyst.infrastructure.moex import InstrumentDTO, MarketType, QuoteDTO

__all__ = [
    "InstrumentAnalysis",
    "MarketOverview",
    "ScoredInstrument",
    "WatchedInstrument",
    "Watchlist",
]


@dataclass(frozen=True, slots=True)
class InstrumentAnalysis:
    """Full analysis of a single instrument for the ``/analyze`` command."""

    ticker: str
    timeframe: Timeframe
    analysis: AnalysisResult
    alerts: tuple[Alert, ...]
    # Best-effort enrichment — ``None`` when ISS omitted the data (e.g. closed
    # board) or the endpoint failed; the core analysis is always present.
    instrument: InstrumentDTO | None = None
    quote: QuoteDTO | None = None


@dataclass(frozen=True, slots=True)
class ScoredInstrument:
    """One instrument's analysis plus its ranking score, for market views."""

    analysis: AnalysisResult
    alert_count: int
    # Bullishness in [-1, 1]: positive = net bullish, negative = net bearish.
    score: float


@dataclass(frozen=True, slots=True)
class MarketOverview:
    """Ranked snapshot of every tracked instrument at one timeframe."""

    timeframe: Timeframe
    # Sorted best-first (descending ``score``).
    scored: tuple[ScoredInstrument, ...]
    # Tickers that could not be analysed this run (ISS error / too little data).
    failed: tuple[str, ...]

    @property
    def best(self) -> ScoredInstrument | None:
        return self.scored[0] if self.scored else None

    @property
    def worst(self) -> ScoredInstrument | None:
        return self.scored[-1] if self.scored else None


@dataclass(frozen=True, slots=True)
class WatchedInstrument:
    """A tracked instrument as exposed to the user's watchlist."""

    ticker: str
    secid: str
    market_type: MarketType


@dataclass(frozen=True, slots=True)
class Watchlist:
    """The set of instruments the platform tracks."""

    instruments: tuple[WatchedInstrument, ...]
