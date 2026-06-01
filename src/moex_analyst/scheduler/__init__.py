"""Scheduled job definitions and service functions for the APScheduler process.

Public surface
--------------
* :mod:`~.registry` — ``JobDef`` dataclass and the five schedule definitions.
* :mod:`~.services` — the five async job functions (individually testable).
"""

from moex_analyst.scheduler.registry import (
    ALERT_GENERATION,
    DAILY_SUMMARY,
    FORECAST_VALIDATION,
    INSTRUMENT_ANALYSIS,
    MARKET_REFRESH,
    JobDef,
    get_all_jobs,
)
from moex_analyst.scheduler.services import (
    alert_generation,
    analyze_all,
    daily_summary,
    forecast_validation,
    market_refresh,
)

__all__ = [
    "ALERT_GENERATION",
    "DAILY_SUMMARY",
    "FORECAST_VALIDATION",
    "INSTRUMENT_ANALYSIS",
    "MARKET_REFRESH",
    "JobDef",
    "alert_generation",
    "analyze_all",
    "daily_summary",
    "forecast_validation",
    "get_all_jobs",
    "market_refresh",
]
