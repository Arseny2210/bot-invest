"""Scheduler process entry point — periodic background jobs via APScheduler.

Console script: ``moex-scheduler`` (see ``pyproject.toml``).

Responsibilities
----------------
* Load settings, configure logging and build the dishka container.
* Resolve dependencies and bind them to the five job functions.
* Register jobs with the :class:`AsyncIOScheduler` according to the schedule
  definitions in :mod:`moex_analyst.scheduler.registry`.
* Catch all job failures at the scheduler boundary so a single exception
  never stops the scheduler (constraint 5).
* Wait for ``SIGINT`` / ``SIGTERM`` and shut down gracefully (constraint 4).
"""

from __future__ import annotations

import asyncio
import signal
from typing import TYPE_CHECKING, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from moex_analyst.application.use_cases import (
    AnalyzeInstrumentUseCase,
    MarketOverviewUseCase,
)
from moex_analyst.core.logging import configure_logging
from moex_analyst.core.settings import get_settings
from moex_analyst.di import make_container
from moex_analyst.infrastructure.moex import CandleService
from moex_analyst.scheduler.registry import get_all_jobs
from moex_analyst.scheduler.services import (
    alert_generation,
    analyze_all,
    daily_summary,
    forecast_validation,
    market_refresh,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from dishka import AsyncContainer

__all__ = ["run"]

# ---------------------------------------------------------------------------
# Job-function-to-name mapping  (architecture: every registry entry must
# have a corresponding entry here).
# ---------------------------------------------------------------------------
_JOB_FUNCS: dict[str, Callable[..., Awaitable[None]]] = {
    "market_refresh": market_refresh,
    "instrument_analysis": analyze_all,
    "alert_generation": alert_generation,
    "daily_summary": daily_summary,
    "forecast_validation": forecast_validation,
}


def _safe_job(
    name: str,
    func: Callable[..., Awaitable[None]],
    **bound: Any,
) -> Callable[[], Awaitable[None]]:
    """Return a nullary wrapper that catches exceptions from ``func``.

    The wrapper is what APScheduler actually invokes.  Any exception raised
    by the job is caught and logged, preventing the scheduler from stopping.
    """

    async def wrapper() -> None:
        log = logger.bind(job=name)
        try:
            await func(**bound)
        except Exception:
            log.exception("Job failed")

    wrapper.__name__ = name
    return wrapper


def _register_jobs(
    scheduler: AsyncIOScheduler,
    *,
    analyze_uc: AnalyzeInstrumentUseCase,
    market_uc: MarketOverviewUseCase,
    candle_svc: CandleService,
) -> None:
    """Register every job from the registry with the scheduler.

    Each job gets its dependencies injected and is wrapped with
    :func:`_safe_job` so that exceptions never propagate to APScheduler.
    """
    deps_map: dict[str, dict[str, Any]] = {
        "market_refresh": {"candle_service": candle_svc},
        "instrument_analysis": {"analyze_uc": analyze_uc},
        "alert_generation": {"analyze_uc": analyze_uc},
        "daily_summary": {"market_uc": market_uc},
        "forecast_validation": {},
    }

    for job_def in get_all_jobs():
        func = _JOB_FUNCS[job_def.name]
        bound_kwargs = deps_map[job_def.name]
        scheduler.add_job(
            _safe_job(job_def.name, func, **bound_kwargs),
            trigger=job_def.trigger,
            **job_def.kwargs,
            id=job_def.name,
            replace_existing=True,
            name=job_def.name,
        )


async def _main() -> None:
    """Configure and run the scheduler until a shutdown signal is received."""
    settings = get_settings()
    configure_logging(settings, service="scheduler")
    log = logger.bind(service="scheduler")

    container: AsyncContainer = make_container(settings)
    scheduler = AsyncIOScheduler()
    stop_event = asyncio.Event()

    try:
        analyze_uc = await container.get(AnalyzeInstrumentUseCase)
        market_uc = await container.get(MarketOverviewUseCase)
        candle_svc = await container.get(CandleService)

        _register_jobs(
            scheduler,
            analyze_uc=analyze_uc,
            market_uc=market_uc,
            candle_svc=candle_svc,
        )

        # Graceful shutdown: SIGINT (Ctrl+C) and SIGTERM (Docker stop).
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)

        scheduler.start()
        log.info(
            "Scheduler started with {} job(s)",
            len(scheduler.get_jobs()),
        )
        await stop_event.wait()
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)
        await container.close()
        log.info("Scheduler stopped")


def run() -> None:
    """Synchronous console-script entry point (see ``pyproject.toml``)."""
    asyncio.run(_main())
