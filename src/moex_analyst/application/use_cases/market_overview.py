"""Use case: rank every tracked instrument by analysed bullishness.

Powers ``/market`` (full ranked list), ``/best`` and ``/worst`` (slices of the
same ranking). Each instrument is analysed independently and concurrently;
per-instrument failures are collected rather than aborting the whole overview.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from moex_analyst.application.use_cases._common import (
    lookback_date_from,
    score_bullishness,
    tracked_tickers,
)
from moex_analyst.application.use_cases.dto import MarketOverview, ScoredInstrument
from moex_analyst.domain.market.timeframe import Timeframe
from moex_analyst.infrastructure.moex.mapping import candle_series_to_domain

if TYPE_CHECKING:
    from moex_analyst.domain.alerts import AlertDetector
    from moex_analyst.domain.analysis import AnalysisEngine
    from moex_analyst.infrastructure.moex import CandleService

__all__ = ["MarketOverviewUseCase"]


class MarketOverviewUseCase:
    """Analyse all tracked instruments and rank them best-first."""

    def __init__(
        self,
        candles: CandleService,
        engine: AnalysisEngine,
        detector: AlertDetector,
    ) -> None:
        self._candles = candles
        self._engine = engine
        self._detector = detector

    async def execute(self, timeframe: Timeframe = Timeframe.D1) -> MarketOverview:
        """Analyse every tracked ticker; return the ranking plus any failures."""
        tickers = tracked_tickers()
        outcomes = await asyncio.gather(
            *(self._analyse_one(t, timeframe) for t in tickers),
            return_exceptions=False,
        )

        scored: list[ScoredInstrument] = []
        failed: list[str] = []
        for ticker, outcome in zip(tickers, outcomes, strict=True):
            if outcome is None:
                failed.append(ticker)
            else:
                scored.append(outcome)

        scored.sort(key=lambda s: s.score, reverse=True)
        return MarketOverview(
            timeframe=timeframe,
            scored=tuple(scored),
            failed=tuple(failed),
        )

    async def _analyse_one(
        self,
        ticker: str,
        timeframe: Timeframe,
    ) -> ScoredInstrument | None:
        """Analyse a single ticker, swallowing failures into ``None``.

        A ticker can legitimately fail an overview run (ISS hiccup, a board with
        too little history); that must not sink the other instruments.
        """
        try:
            series_dto = await self._candles.get_candles(
                ticker, timeframe, date_from=lookback_date_from(timeframe),
            )
            analysis = self._engine.analyse(candle_series_to_domain(series_dto))
        except Exception:  # overview is resilient: one bad ticker must not sink it
            return None

        alerts = self._detector.detect(analysis)
        return ScoredInstrument(
            analysis=analysis,
            alert_count=len(alerts),
            score=score_bullishness(analysis),
        )
