"""Tests for the scheduler job functions — each tested with mocked dependencies."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from moex_analyst.application.use_cases.dto import MarketOverview
from moex_analyst.domain.market.timeframe import Timeframe
from moex_analyst.scheduler.services import (
    alert_generation,
    analyze_all,
    daily_summary,
    forecast_validation,
    market_refresh,
)

_FAKE_TICKERS = ("IMOEX", "VTBR")


@pytest.fixture(autouse=True)
def _patch_tickers() -> None:
    """Use a short, predictable ticker list for all tests in this module."""
    with patch(
        "moex_analyst.scheduler.services.tracked_tickers",
        return_value=_FAKE_TICKERS,
    ):
        yield


# ---------------------------------------------------------------------------
# market_refresh
# ---------------------------------------------------------------------------


class TestMarketRefresh:
    async def test_fetches_all_tickers_and_timeframes(self) -> None:
        candle_service = AsyncMock()
        await market_refresh(candle_service)

        # 2 tickers x 3 timeframes = 6 calls
        assert candle_service.get_candles.call_count == 6

    async def test_passes_lookback_date(self) -> None:
        candle_service = AsyncMock()
        await market_refresh(candle_service)

        for call in candle_service.get_candles.call_args_list:
            _args, kwargs = call
            assert "date_from" in kwargs

    async def test_continues_on_ticker_error(self) -> None:
        candle_service = AsyncMock()
        candle_service.get_candles.side_effect = [
            ValueError("boom"),
            AsyncMock(),
            AsyncMock(),
            AsyncMock(),
            AsyncMock(),
            AsyncMock(),
        ]
        await market_refresh(candle_service)

        # Even though the first call failed, the remaining 5 should proceed.
        assert candle_service.get_candles.call_count == 6

    async def test_continues_on_timeframe_error(self) -> None:
        candle_service = AsyncMock()
        candle_service.get_candles.side_effect = [
            AsyncMock(),
            ValueError("boom"),
            AsyncMock(),
            AsyncMock(),
            AsyncMock(),
            AsyncMock(),
        ]
        await market_refresh(candle_service)

        assert candle_service.get_candles.call_count == 6


# ---------------------------------------------------------------------------
# analyze_all
# ---------------------------------------------------------------------------


class TestAnalyzeAll:
    async def test_analyzes_every_ticker(self) -> None:
        analyze_uc = AsyncMock()
        analyze_uc.execute.return_value = AsyncMock()

        await analyze_all(analyze_uc)

        assert analyze_uc.execute.call_count == 2
        # verify ticker arguments
        called_tickers = [call.args[0] for call in analyze_uc.execute.call_args_list]
        assert called_tickers == ["IMOEX", "VTBR"]

    async def test_continues_on_ticker_error(self) -> None:
        analyze_uc = AsyncMock()
        analyze_uc.execute.side_effect = [ValueError("boom"), AsyncMock()]

        await analyze_all(analyze_uc)

        assert analyze_uc.execute.call_count == 2


# ---------------------------------------------------------------------------
# alert_generation
# ---------------------------------------------------------------------------


class TestAlertGeneration:
    async def test_analyzes_every_ticker(self) -> None:
        analyze_uc = AsyncMock()
        analysis = AsyncMock()
        analysis.alerts = ()
        analyze_uc.execute.return_value = analysis

        await alert_generation(analyze_uc)

        assert analyze_uc.execute.call_count == 2

    async def test_logs_alert_count_when_alerts_present(self) -> None:
        analyze_uc = AsyncMock()
        analysis = MagicMock()
        analysis.alerts = ("alert1", "alert2")
        analyze_uc.execute.return_value = analysis

        with patch("moex_analyst.scheduler.services.logger.bind") as mock_bind:
            mock_log = MagicMock()
            mock_bind.return_value = mock_log
            await alert_generation(analyze_uc)

        mock_log.info.assert_any_call("{}: {} alert(s)", "IMOEX", 2)

    async def test_continues_on_ticker_error(self) -> None:
        analyze_uc = AsyncMock()
        analyze_uc.execute.side_effect = [ValueError("boom"), AsyncMock()]

        await alert_generation(analyze_uc)

        assert analyze_uc.execute.call_count == 2


# ---------------------------------------------------------------------------
# daily_summary
# ---------------------------------------------------------------------------


class TestDailySummary:
    async def test_generates_market_overview(self) -> None:
        market_uc = AsyncMock()
        overview = MarketOverview(
            timeframe=Timeframe.D1,
            scored=(),
            failed=(),
        )
        market_uc.execute.return_value = overview

        await daily_summary(market_uc)

        market_uc.execute.assert_awaited_once()

    async def test_handles_execution_error(self) -> None:
        market_uc = AsyncMock()
        market_uc.execute.side_effect = RuntimeError("ISS down")

        # Should not propagate the exception
        await daily_summary(market_uc)
        market_uc.execute.assert_awaited_once()


# ---------------------------------------------------------------------------
# forecast_validation
# ---------------------------------------------------------------------------


class TestForecastValidation:
    async def test_does_not_raise(self) -> None:
        await forecast_validation()
