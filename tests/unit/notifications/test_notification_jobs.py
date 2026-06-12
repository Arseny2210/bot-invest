"""Tests for the notification job functions — each tested with mocked dependencies."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from moex_analyst.scheduler.notification_jobs import (
    notify_alert_generation,
    notify_daily_summary,
)

_FAKE_TICKERS = ("IMOEX", "VTBR")


@pytest.fixture(autouse=True)
def _patch_tickers() -> None:
    """Use a short, predictable ticker list for all tests in this module."""
    with patch(
        "moex_analyst.scheduler.notification_jobs.tracked_tickers",
        return_value=_FAKE_TICKERS,
    ):
        yield


class TestNotifyAlertGeneration:
    async def test_analyzes_and_sends_alerts(self) -> None:
        analyze_uc = AsyncMock()
        notifier = AsyncMock()
        analysis = AsyncMock()
        analysis.alerts = ("alert1", "alert2")
        analyze_uc.execute.return_value = analysis

        await notify_alert_generation(
            analyze_uc=analyze_uc,
            notifier=notifier,
            chat_id=12345,
        )

        assert analyze_uc.execute.call_count == 2
        assert notifier.send_alerts.call_count == 2

    async def test_skips_tickers_without_alerts(self) -> None:
        analyze_uc = AsyncMock()
        notifier = AsyncMock()
        analysis = AsyncMock()
        analysis.alerts = ()
        analyze_uc.execute.return_value = analysis

        await notify_alert_generation(
            analyze_uc=analyze_uc,
            notifier=notifier,
            chat_id=12345,
        )

        notifier.send_alerts.assert_not_called()

    async def test_continues_on_ticker_error(self) -> None:
        analyze_uc = AsyncMock()
        notifier = AsyncMock()
        analyze_uc.execute.side_effect = [ValueError("boom"), AsyncMock()]

        await notify_alert_generation(
            analyze_uc=analyze_uc,
            notifier=notifier,
            chat_id=12345,
        )

        assert analyze_uc.execute.call_count == 2


class TestNotifyDailySummary:
    async def test_sends_market_summary(self) -> None:
        market_uc = AsyncMock()
        notifier = AsyncMock()
        overview = MagicMock()
        overview.scored = ()
        overview.failed = ()
        market_uc.execute.return_value = overview

        await notify_daily_summary(
            market_uc=market_uc,
            notifier=notifier,
            chat_id=12345,
        )

        market_uc.execute.assert_awaited_once()
        notifier.send_market_summary.assert_awaited_once_with(
            overview,
            chat_id=12345,
        )

    async def test_handles_execution_error(self) -> None:
        market_uc = AsyncMock()
        notifier = AsyncMock()
        market_uc.execute.side_effect = RuntimeError("ISS down")

        await notify_daily_summary(
            market_uc=market_uc,
            notifier=notifier,
            chat_id=12345,
        )

        market_uc.execute.assert_awaited_once()
        notifier.send_market_summary.assert_not_called()
