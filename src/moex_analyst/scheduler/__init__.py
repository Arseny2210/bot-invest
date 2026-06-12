"""Scheduled job definitions and service functions for the APScheduler process.

Public surface
--------------
* :mod:`~.registry` — ``JobDef`` dataclass and the schedule definitions.
* :mod:`~.services` — the async job functions (individually testable).
* :mod:`~.notification_jobs` — notification delivery job functions.
* :mod:`~.persistence_jobs` — persistence job functions.
"""

from moex_analyst.scheduler.notification_jobs import (
    notify_alert_generation,
    notify_daily_summary,
)
from moex_analyst.scheduler.persistence_jobs import (
    evaluate_forecasts,
    persist_alerts,
    persist_analyses,
)
from moex_analyst.scheduler.registry import (
    ALERT_GENERATION,
    DAILY_SUMMARY,
    EVALUATE_FORECASTS,
    FORECAST_VALIDATION,
    INSTRUMENT_ANALYSIS,
    MARKET_REFRESH,
    NOTIFY_ALERT_GENERATION,
    NOTIFY_DAILY_SUMMARY,
    PERSIST_ALERTS,
    PERSIST_ANALYSES,
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
    "EVALUATE_FORECASTS",
    "FORECAST_VALIDATION",
    "INSTRUMENT_ANALYSIS",
    "MARKET_REFRESH",
    "NOTIFY_ALERT_GENERATION",
    "NOTIFY_DAILY_SUMMARY",
    "PERSIST_ALERTS",
    "PERSIST_ANALYSES",
    "JobDef",
    "alert_generation",
    "analyze_all",
    "daily_summary",
    "evaluate_forecasts",
    "forecast_validation",
    "get_all_jobs",
    "market_refresh",
    "notify_alert_generation",
    "notify_daily_summary",
    "persist_alerts",
    "persist_analyses",
]
