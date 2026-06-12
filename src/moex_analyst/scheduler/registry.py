"""Scheduled job metadata — triggers, schedules, and the :class:`JobDef` model.

Job definitions are decoupled from the service functions that implement them;
the entry point maps names → functions at wiring time. This separation keeps
the schedule definitions pure-data and independently testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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
    "get_all_jobs",
]


@dataclass(frozen=True)
class JobDef:
    """Immutable schedule metadata for one recurring job.

    Attributes:
        name: unique job identifier (used as APScheduler ``id``).
        trigger: APScheduler trigger type (``"interval"`` or ``"cron"``).
        kwargs: keyword arguments passed to the trigger constructor.
    """

    name: str
    trigger: str
    kwargs: dict[str, Any]


MARKET_REFRESH = JobDef(
    name="market_refresh",
    trigger="interval",
    kwargs={"minutes": 15, "jitter": 30},
)

INSTRUMENT_ANALYSIS = JobDef(
    name="instrument_analysis",
    trigger="interval",
    kwargs={"minutes": 15, "jitter": 30},
)

ALERT_GENERATION = JobDef(
    name="alert_generation",
    trigger="interval",
    kwargs={"minutes": 15, "jitter": 30},
)

DAILY_SUMMARY = JobDef(
    name="daily_summary",
    trigger="cron",
    kwargs={"hour": 9, "minute": 0, "timezone": "Europe/Moscow"},
)

FORECAST_VALIDATION = JobDef(
    name="forecast_validation",
    trigger="cron",
    kwargs={"hour": 23, "minute": 0, "timezone": "Europe/Moscow"},
)


NOTIFY_ALERT_GENERATION = JobDef(
    name="notify_alert_generation",
    trigger="interval",
    kwargs={"minutes": 15, "jitter": 30},
)

NOTIFY_DAILY_SUMMARY = JobDef(
    name="notify_daily_summary",
    trigger="cron",
    kwargs={"hour": 9, "minute": 30, "timezone": "Europe/Moscow"},
)

PERSIST_ANALYSES = JobDef(
    name="persist_analyses",
    trigger="interval",
    kwargs={"minutes": 30, "jitter": 60},
)

PERSIST_ALERTS = JobDef(
    name="persist_alerts",
    trigger="interval",
    kwargs={"minutes": 30, "jitter": 60},
)

EVALUATE_FORECASTS = JobDef(
    name="evaluate_forecasts",
    trigger="interval",
    kwargs={"hours": 1, "jitter": 120},
)


def get_all_jobs() -> tuple[JobDef, ...]:
    """Return every scheduled job definition in a stable order."""
    return (
        MARKET_REFRESH,
        INSTRUMENT_ANALYSIS,
        ALERT_GENERATION,
        DAILY_SUMMARY,
        FORECAST_VALIDATION,
        NOTIFY_ALERT_GENERATION,
        NOTIFY_DAILY_SUMMARY,
        PERSIST_ANALYSES,
        PERSIST_ALERTS,
        EVALUATE_FORECASTS,
    )
