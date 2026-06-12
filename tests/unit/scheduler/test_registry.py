"""Tests for the scheduler job registry — metadata and architecture alignment."""

import asyncio

import pytest

from moex_analyst.scheduler import (
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
    alert_generation,
    analyze_all,
    daily_summary,
    evaluate_forecasts,
    forecast_validation,
    get_all_jobs,
    market_refresh,
    notify_alert_generation,
    notify_daily_summary,
    persist_alerts,
    persist_analyses,
)


class TestJobDef:
    def test_frozen_dataclass(self) -> None:
        job = JobDef(name="t", trigger="interval", kwargs={"minutes": 5})
        with pytest.raises(AttributeError):
            job.name = "other"  # type: ignore[misc]

    def test_equality(self) -> None:
        a = JobDef(name="t", trigger="interval", kwargs={"minutes": 5})
        b = JobDef(name="t", trigger="interval", kwargs={"minutes": 5})
        assert a == b

    def test_repr(self) -> None:
        job = JobDef(name="t", trigger="interval", kwargs={"minutes": 5})
        assert "JobDef" in repr(job)
        assert "t" in repr(job)


class TestJobConstants:
    def test_market_refresh_def(self) -> None:
        assert MARKET_REFRESH.name == "market_refresh"
        assert MARKET_REFRESH.trigger == "interval"
        assert MARKET_REFRESH.kwargs == {"minutes": 15, "jitter": 30}

    def test_instrument_analysis_def(self) -> None:
        assert INSTRUMENT_ANALYSIS.name == "instrument_analysis"
        assert INSTRUMENT_ANALYSIS.trigger == "interval"
        assert INSTRUMENT_ANALYSIS.kwargs == {"minutes": 15, "jitter": 30}

    def test_alert_generation_def(self) -> None:
        assert ALERT_GENERATION.name == "alert_generation"
        assert ALERT_GENERATION.trigger == "interval"
        assert ALERT_GENERATION.kwargs == {"minutes": 15, "jitter": 30}

    def test_daily_summary_def(self) -> None:
        assert DAILY_SUMMARY.name == "daily_summary"
        assert DAILY_SUMMARY.trigger == "cron"
        assert DAILY_SUMMARY.kwargs == {
            "hour": 9,
            "minute": 0,
            "timezone": "Europe/Moscow",
        }

    def test_forecast_validation_def(self) -> None:
        assert FORECAST_VALIDATION.name == "forecast_validation"
        assert FORECAST_VALIDATION.trigger == "cron"
        assert FORECAST_VALIDATION.kwargs == {
            "hour": 23,
            "minute": 0,
            "timezone": "Europe/Moscow",
        }

    def test_notify_alert_generation_def(self) -> None:
        assert NOTIFY_ALERT_GENERATION.name == "notify_alert_generation"
        assert NOTIFY_ALERT_GENERATION.trigger == "interval"
        assert NOTIFY_ALERT_GENERATION.kwargs == {"minutes": 15, "jitter": 30}

    def test_notify_daily_summary_def(self) -> None:
        assert NOTIFY_DAILY_SUMMARY.name == "notify_daily_summary"
        assert NOTIFY_DAILY_SUMMARY.trigger == "cron"
        assert NOTIFY_DAILY_SUMMARY.kwargs == {
            "hour": 9,
            "minute": 30,
            "timezone": "Europe/Moscow",
        }

    def test_persist_analyses_def(self) -> None:
        assert PERSIST_ANALYSES.name == "persist_analyses"
        assert PERSIST_ANALYSES.trigger == "interval"
        assert PERSIST_ANALYSES.kwargs == {"minutes": 30, "jitter": 60}

    def test_persist_alerts_def(self) -> None:
        assert PERSIST_ALERTS.name == "persist_alerts"
        assert PERSIST_ALERTS.trigger == "interval"
        assert PERSIST_ALERTS.kwargs == {"minutes": 30, "jitter": 60}

    def test_evaluate_forecasts_def(self) -> None:
        assert EVALUATE_FORECASTS.name == "evaluate_forecasts"
        assert EVALUATE_FORECASTS.trigger == "interval"
        assert EVALUATE_FORECASTS.kwargs == {"hours": 1, "jitter": 120}


class TestGetAllJobs:
    def test_returns_ten(self) -> None:
        jobs = get_all_jobs()
        assert len(jobs) == 10

    def test_all_names_unique(self) -> None:
        jobs = get_all_jobs()
        names = [j.name for j in jobs]
        assert len(names) == len(set(names))

    def test_all_triggers_valid(self) -> None:
        jobs = get_all_jobs()
        for j in jobs:
            assert j.trigger in ("interval", "cron")

    def test_interval_jobs_have_minutes_or_hours(self) -> None:
        for j in get_all_jobs():
            if j.trigger == "interval":
                assert "minutes" in j.kwargs or "hours" in j.kwargs

    def test_cron_jobs_have_hour_minute_timezone(self) -> None:
        for j in get_all_jobs():
            if j.trigger == "cron":
                assert "hour" in j.kwargs
                assert "minute" in j.kwargs
                assert "timezone" in j.kwargs

    def test_stable_order(self) -> None:
        assert get_all_jobs() == get_all_jobs()


class TestArchitecture:
    """Verify that every registry job has a corresponding service function.

    This is the scheduler architecture test (constraint 6): the registry
    and the service layer must stay in sync.  If a new JobDef is added but
    no service function exists (or vice versa), this test fails.
    """

    def test_every_job_has_matching_service_function(self) -> None:
        func_map: dict[str, object] = {
            "market_refresh": market_refresh,
            "instrument_analysis": analyze_all,
            "alert_generation": alert_generation,
            "daily_summary": daily_summary,
            "forecast_validation": forecast_validation,
            "notify_alert_generation": notify_alert_generation,
            "notify_daily_summary": notify_daily_summary,
            "persist_analyses": persist_analyses,
            "persist_alerts": persist_alerts,
            "evaluate_forecasts": evaluate_forecasts,
        }
        for job in get_all_jobs():
            assert job.name in func_map, f"Job {job.name!r} has no matching service function"
            assert callable(func_map[job.name])

    def test_market_refresh_is_async(self) -> None:
        assert asyncio.iscoroutinefunction(market_refresh)

    def test_all_service_functions_are_async(self) -> None:
        funcs = [
            market_refresh,
            analyze_all,
            alert_generation,
            daily_summary,
            forecast_validation,
            notify_alert_generation,
            notify_daily_summary,
            persist_analyses,
            persist_alerts,
            evaluate_forecasts,
        ]
        for fn in funcs:
            assert asyncio.iscoroutinefunction(fn), f"{fn.__name__} is not async"
