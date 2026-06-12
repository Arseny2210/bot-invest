"""Scheduled notification job functions — deliver alerts via ``NotifierPort``.

Each function is a plain async callable that receives its dependencies as
keyword arguments, following the same pattern as :mod:`.services`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from moex_analyst.application.use_cases._common import tracked_tickers

if TYPE_CHECKING:
    from moex_analyst.application.ports.notifier import NotifierPort
    from moex_analyst.application.use_cases import (
        AnalyzeInstrumentUseCase,
        MarketOverviewUseCase,
    )

__all__ = [
    "notify_alert_generation",
    "notify_daily_summary",
]


async def notify_alert_generation(
    analyze_uc: AnalyzeInstrumentUseCase,
    notifier: NotifierPort,
    chat_id: int,
) -> None:
    """Analyse all instruments and send new alerts to the notification chat.

    Per-ticker exceptions are caught and logged so a single failure does not
    abort the batch.
    """
    log = logger.bind(job="notify_alert_generation")
    tickers = tracked_tickers()
    log.info("Checking {} tickers for new alerts", len(tickers))
    for ticker in tickers:
        try:
            result = await analyze_uc.execute(ticker)
            if result.alerts:
                await notifier.send_alerts(result.alerts, chat_id=chat_id)
                log.info("Sent {} alert(s) for {}", len(result.alerts), ticker)
        except Exception:
            log.exception("Failed to check/send alerts for {}", ticker)


async def notify_daily_summary(
    market_uc: MarketOverviewUseCase,
    notifier: NotifierPort,
    chat_id: int,
) -> None:
    """Generate the daily market overview and send it to the notification chat."""
    log = logger.bind(job="notify_daily_summary")
    log.info("Generating and sending daily market summary")
    try:
        overview = await market_uc.execute()
        await notifier.send_market_summary(overview, chat_id=chat_id)
        log.info(
            "Sent market summary ({} scored, {} failed, timeframe={})",
            len(overview.scored),
            len(overview.failed),
            overview.timeframe.value,
        )
    except Exception:
        log.exception("Failed to send daily market summary")
