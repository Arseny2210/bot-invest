"""Scheduled job functions — business logic without APScheduler coupling.

Each function is a plain async callable that receives its dependencies as
keyword arguments.  The scheduler entry point resolves dependencies from the
dishka container and binds them before passing the function to APScheduler.
This makes every job individually testable with mocked dependencies.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from loguru import logger

from moex_analyst.application.use_cases._common import tracked_tickers
from moex_analyst.domain.market.timeframe import Timeframe

if TYPE_CHECKING:
    from moex_analyst.application.use_cases import (
        AnalyzeInstrumentUseCase,
        MarketOverviewUseCase,
    )
    from moex_analyst.infrastructure.moex import CandleService

__all__ = [
    "alert_generation",
    "analyze_all",
    "daily_summary",
    "forecast_validation",
    "market_refresh",
]

# Calendar-day lookback for the market-refresh pre-fetch — generous enough
# to return recent data without the overhead of the full analysis lookback.
_REFRESH_LOOKBACK_DAYS: int = 30


async def market_refresh(candle_service: CandleService) -> None:
    """Pre-fetch candle data for all tracked instruments across timeframes.

    Keeps the ISS connection warm and prepares data for any future caching
    layer (Stage 11).  Per-ticker failures are caught and logged so a single
    problematic instrument never aborts the refresh cycle.
    """
    log = logger.bind(job="market_refresh")
    tickers = tracked_tickers()
    timeframes = (Timeframe.H1, Timeframe.H4, Timeframe.D1)
    lookback = (datetime.now(UTC) - timedelta(days=_REFRESH_LOOKBACK_DAYS)).date()
    log.info("Refreshing {} tickers across {} timeframe(s)", len(tickers), len(timeframes))
    for ticker in tickers:
        for tf in timeframes:
            try:
                await candle_service.get_candles(ticker, tf, date_from=lookback)
            except Exception:
                log.exception("Failed to refresh {} @ {}", ticker, tf.value)


async def analyze_all(analyze_uc: AnalyzeInstrumentUseCase) -> None:
    """Run full analysis on every tracked instrument at D1.

    Per-ticker exceptions are caught and logged so that a single
    problematic instrument does not abort the batch.
    """
    log = logger.bind(job="analyze_all")
    tickers = tracked_tickers()
    log.info("Analyzing {} tickers", len(tickers))
    for ticker in tickers:
        try:
            await analyze_uc.execute(ticker)
        except Exception:
            log.exception("Failed to analyze {}", ticker)


async def alert_generation(analyze_uc: AnalyzeInstrumentUseCase) -> None:
    """Analyse all instruments and log detected alert counts.

    Shares the same underlying analysis as ``analyze_all`` but runs on an
    offset schedule and explicitly records how many alerts each instrument
    triggered.
    """
    log = logger.bind(job="alert_generation")
    tickers = tracked_tickers()
    for ticker in tickers:
        try:
            result = await analyze_uc.execute(ticker)
            if result.alerts:
                log.info("{}: {} alert(s)", ticker, len(result.alerts))
        except Exception:
            log.exception("Failed to check alerts for {}", ticker)


async def daily_summary(market_uc: MarketOverviewUseCase) -> None:
    """Generate and log the daily market overview ranking.

    The summary statistics (scored / failed count, timeframe) are recorded
    for observability.
    """
    log = logger.bind(job="daily_summary")
    log.info("Generating daily market summary")
    try:
        overview = await market_uc.execute()
        log.info(
            "Analysed {} instruments, {} failed (timeframe={})",
            len(overview.scored),
            len(overview.failed),
            overview.timeframe.value,
        )
    except Exception:
        log.exception("Daily summary failed")


async def forecast_validation() -> None:
    """Placeholder: validate past analysis predictions against actual prices.

    No-op until persistence (Stage 11) provides stored analysis snapshots
    that can be compared with subsequent market movements.
    """
    logger.bind(job="forecast_validation").info(
        "Forecast validation skipped — persistence not available",
    )
