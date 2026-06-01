"""Application use cases — orchestration over domain + infrastructure services.

Each use case combines the existing services (MOEX data services, the analysis
engine, the alert detector) into a single operation the presentation layer can
call, returning the application DTOs in :mod:`.dto`.
"""

from __future__ import annotations

from moex_analyst.application.use_cases.analyze_instrument import AnalyzeInstrumentUseCase
from moex_analyst.application.use_cases.dto import (
    InstrumentAnalysis,
    MarketOverview,
    ScoredInstrument,
    WatchedInstrument,
    Watchlist,
)
from moex_analyst.application.use_cases.market_overview import MarketOverviewUseCase
from moex_analyst.application.use_cases.watchlist import WatchlistUseCase

__all__ = [
    "AnalyzeInstrumentUseCase",
    "InstrumentAnalysis",
    "MarketOverview",
    "MarketOverviewUseCase",
    "ScoredInstrument",
    "WatchedInstrument",
    "Watchlist",
    "WatchlistUseCase",
]
