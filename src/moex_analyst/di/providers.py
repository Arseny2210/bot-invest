"""Dishka providers — the application's dependency graph.

A single :class:`AppProvider` wires the whole object graph at ``APP`` scope:
the shared MOEX HTTP client (closed on container shutdown), the three MOEX
services, the stateless analysis/alert engines, and the use cases that compose
them. ``Settings`` is supplied as container context at creation time.

All components here are stateless and concurrency-safe, so a single instance of
each is shared process-wide — which is exactly what ``APP`` scope provides.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from dishka import Provider, Scope, from_context, provide

from moex_analyst.application.use_cases import (
    AnalyzeInstrumentUseCase,
    MarketOverviewUseCase,
    WatchlistUseCase,
)
from moex_analyst.core.settings import Settings
from moex_analyst.domain.alerts import AlertDetector
from moex_analyst.domain.analysis import AnalysisEngine
from moex_analyst.infrastructure.moex import (
    CandleService,
    InstrumentService,
    MoexHttpClient,
    QuoteService,
)

__all__ = ["AppProvider"]


class AppProvider(Provider):
    """Provides every dependency the bot (and future processes) need."""

    settings = from_context(provides=Settings, scope=Scope.APP)

    # --- MOEX transport + services -----------------------------------------
    @provide(scope=Scope.APP)
    async def http_client(self, settings: Settings) -> AsyncIterator[MoexHttpClient]:
        """Shared ISS client; closed when the container is closed."""
        client = MoexHttpClient(settings.moex)
        try:
            yield client
        finally:
            await client.aclose()

    @provide(scope=Scope.APP)
    def candle_service(self, client: MoexHttpClient) -> CandleService:
        return CandleService(client)

    @provide(scope=Scope.APP)
    def quote_service(self, client: MoexHttpClient) -> QuoteService:
        return QuoteService(client)

    @provide(scope=Scope.APP)
    def instrument_service(self, client: MoexHttpClient) -> InstrumentService:
        return InstrumentService(client)

    # --- domain engines (stateless) ----------------------------------------
    @provide(scope=Scope.APP)
    def analysis_engine(self) -> AnalysisEngine:
        return AnalysisEngine()

    @provide(scope=Scope.APP)
    def alert_detector(self) -> AlertDetector:
        return AlertDetector()

    # --- use cases ----------------------------------------------------------
    @provide(scope=Scope.APP)
    def analyze_use_case(
        self,
        candles: CandleService,
        quotes: QuoteService,
        instruments: InstrumentService,
        engine: AnalysisEngine,
        detector: AlertDetector,
    ) -> AnalyzeInstrumentUseCase:
        return AnalyzeInstrumentUseCase(candles, quotes, instruments, engine, detector)

    @provide(scope=Scope.APP)
    def market_overview_use_case(
        self,
        candles: CandleService,
        engine: AnalysisEngine,
        detector: AlertDetector,
    ) -> MarketOverviewUseCase:
        return MarketOverviewUseCase(candles, engine, detector)

    @provide(scope=Scope.APP)
    def watchlist_use_case(self) -> WatchlistUseCase:
        return WatchlistUseCase()
