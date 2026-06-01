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
    "FORECAST_VALIDATION",
    "INSTRUMENT_ANALYSIS",
    "MARKET_REFRESH",
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


def get_all_jobs() -> tuple[JobDef, ...]:
    """Return every scheduled job definition in a stable order."""
    return (
        MARKET_REFRESH,
        INSTRUMENT_ANALYSIS,
        ALERT_GENERATION,
        DAILY_SUMMARY,
        FORECAST_VALIDATION,
    )
