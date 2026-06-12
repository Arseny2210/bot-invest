"""Scheduled persistence job functions — persist analysis outputs to the database.

Each function receives its dependencies as keyword arguments, following the
same pattern as :mod:`.services` and :mod:`.notification_jobs`.
"""

from __future__ import annotations

from hashlib import sha256
from typing import TYPE_CHECKING, Any

from loguru import logger

from moex_analyst.application.use_cases._common import tracked_tickers
from moex_analyst.domain.market.timeframe import Timeframe
from moex_analyst.infrastructure.db.models import AlertRecord, AnalysisRecord
from moex_analyst.infrastructure.db.repositories.alert_repository import (
    AlertRepository,
)
from moex_analyst.infrastructure.db.repositories.analysis_repository import (
    AnalysisRepository,
)
from moex_analyst.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from moex_analyst.application.services.forecast_tracking import (
        ForecastTrackingService,
    )
    from moex_analyst.application.use_cases import AnalyzeInstrumentUseCase
    from moex_analyst.domain.alerts import Alert
    from moex_analyst.domain.analysis import AnalysisResult
    from moex_analyst.infrastructure.moex import QuoteService

__all__ = [
    "evaluate_forecasts",
    "persist_alerts",
    "persist_analyses",
]


async def persist_analyses(
    analyze_uc: AnalyzeInstrumentUseCase,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Run analysis on all instruments and persist every result.

    Per-ticker exceptions are caught and logged so a single failure does not
    abort the batch.
    """
    log = logger.bind(job="persist_analyses")
    tickers = tracked_tickers()
    timeframes = (Timeframe.H1, Timeframe.H4, Timeframe.D1)
    log.info("Persisting analyses for {} tickers x {} timeframe(s)", len(tickers), len(timeframes))
    saved = 0
    for ticker in tickers:
        for tf in timeframes:
            try:
                result = await analyze_uc.execute(ticker, timeframe=tf)
                await _save_analysis(session_factory, result.analysis)
                await _save_alerts(session_factory, result.alerts)
                saved += 1
            except Exception:
                log.exception("Failed to persist analysis for {} @ {}", ticker, tf.value)
    log.info("Persisted {} analysis snapshots", saved)


async def persist_alerts(
    analyze_uc: AnalyzeInstrumentUseCase,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Run alert generation on all instruments and persist every alert.

    Per-ticker exceptions are caught and logged.
    """
    log = logger.bind(job="persist_alerts")
    tickers = tracked_tickers()
    log.info("Persisting alerts for {} tickers", len(tickers))
    total_alerts = 0
    for ticker in tickers:
        try:
            result = await analyze_uc.execute(ticker)
            if result.alerts:
                await _save_alerts(session_factory, result.alerts)
                total_alerts += len(result.alerts)
        except Exception:
            log.exception("Failed to persist alerts for {}", ticker)
    log.info("Persisted {} alert(s)", total_alerts)


async def evaluate_forecasts(
    forecast_service: ForecastTrackingService,
    quote_service: QuoteService,
) -> None:
    """Evaluate any pending forecasts whose horizon has elapsed.

    Fetches the current quote for each forecast's ticker and evaluates it.
    """
    log = logger.bind(job="evaluate_forecasts")
    try:
        pending = await forecast_service.find_ready_for_evaluation()
        if not pending:
            log.info("No forecasts ready for evaluation")
            return
        log.info("Evaluating {} forecast(s)", len(pending))
        evaluated = 0
        for forecast in pending:
            try:
                quote = await quote_service.get_quote(forecast.ticker)
                if quote is None or quote.last is None:
                    log.warning("No quote for {}, skipping", forecast.ticker)
                    continue
                predicted_dir = (
                    "bullish"
                    if forecast.bullish_probability >= forecast.bearish_probability
                    else "bearish"
                )
                await forecast_service.evaluate_forecast(
                    forecast.id,
                    actual_price=quote.last,
                    predicted_direction=predicted_dir,
                )
                evaluated += 1
            except Exception:
                log.exception("Failed to evaluate forecast #{}", forecast.id)
        log.info("Evaluated {} forecast(s)", evaluated)
    except Exception:
        log.exception("Failed to evaluate forecasts")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _save_analysis(
    session_factory: async_sessionmaker[AsyncSession],
    analysis: AnalysisResult,
) -> AnalysisRecord:
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repo = AnalysisRepository(uow.session)
        record = AnalysisRecord(
            ticker=analysis.ticker,
            timeframe=analysis.timeframe.value,
            as_of=analysis.as_of,
            trend_direction=analysis.trend.direction.value,
            trend_strength=analysis.trend.strength.value,
            trend_score=analysis.trend.score,
            bullish_probability=analysis.probabilities.bullish,
            bearish_probability=analysis.probabilities.bearish,
            sideways_probability=analysis.probabilities.sideways,
            rsi=analysis.indicators.rsi14,
            atr=analysis.indicators.atr14,
            ema20=analysis.indicators.ema20,
            ema50=analysis.indicators.ema50,
            support_levels=[_level_to_dict(lev) for lev in analysis.support_levels],
            resistance_levels=[_level_to_dict(lev) for lev in analysis.resistance_levels],
            volume_state=analysis.volume_condition.value,
            market_structure=", ".join(analysis.structure.labels),
            candles_analysed=analysis.candles_analysed,
        )
        await repo.add(record)
        await uow.commit()
        return record


async def _save_alerts(
    session_factory: async_sessionmaker[AsyncSession],
    alerts: Sequence[Alert],
) -> list[AlertRecord]:
    if not alerts:
        return []
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repo = AlertRepository(uow.session)
        records = [
            AlertRecord(
                ticker=a.ticker,
                timeframe=a.timeframe.value,
                alert_type=a.type.value,
                direction=a.direction.value,
                severity=a.severity.value,
                score=a.score,
                message_hash=_hash_message(a.message),
                as_of=a.as_of,
            )
            for a in alerts
        ]
        await repo.add_all(records)
        await uow.commit()
        return list(records)


def _level_to_dict(level: Any) -> dict[str, Any]:
    return {
        "kind": level.kind.value,
        "price": str(level.price),
        "touches": level.touches,
        "strength": level.strength,
    }


def _hash_message(message: str) -> str:
    return sha256(message.encode("utf-8")).hexdigest()
