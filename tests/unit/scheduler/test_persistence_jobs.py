"""Tests for the persistence job functions — mocked dependencies."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from moex_analyst.scheduler.persistence_jobs import (
    evaluate_forecasts,
    persist_alerts,
    persist_analyses,
)

_FAKE_TICKERS = ("IMOEX", "VTBR")


@pytest.fixture(autouse=True)
def _patch_tickers() -> None:
    with patch(
        "moex_analyst.scheduler.persistence_jobs.tracked_tickers",
        return_value=_FAKE_TICKERS,
    ):
        yield


class TestPersistAnalyses:
    async def test_analyzes_all_tickers_and_timeframes(self) -> None:
        analyze_uc = AsyncMock()
        session_factory = AsyncMock()
        session = AsyncMock()
        session.commit = AsyncMock()
        session.flush = AsyncMock()
        session_factory.return_value.__aenter__.return_value = session

        analysis = MagicMock()
        analysis.alerts = ()
        analysis.ticker = "IMOEX"
        analysis.timeframe = MagicMock(value="1D")
        analysis.as_of = None
        analysis.trend.direction.value = "up"
        analysis.trend.strength.value = "strong"
        analysis.trend.score = 0.5
        analysis.probabilities.bullish = 0.6
        analysis.probabilities.bearish = 0.2
        analysis.probabilities.sideways = 0.2
        analysis.indicators.rsi14 = None
        analysis.indicators.atr14 = None
        analysis.indicators.ema20 = None
        analysis.indicators.ema50 = None
        analysis.support_levels = ()
        analysis.resistance_levels = ()
        analysis.volume_condition.value = "normal"
        analysis.structure.labels = ()
        analysis.candles_analysed = 60
        analyze_uc.execute.return_value = type("R", (), {"analysis": analysis, "alerts": ()})()

        mock_exec_result = MagicMock()
        mock_exec_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_exec_result)
        session.get = AsyncMock(return_value=None)

        await persist_analyses(
            analyze_uc=analyze_uc,
            session_factory=session_factory,
        )

        assert analyze_uc.execute.call_count > 0


class TestPersistAlerts:
    async def test_analyzes_and_persists_alerts(self) -> None:
        analyze_uc = AsyncMock()
        session_factory = AsyncMock()
        session = AsyncMock()
        session.commit = AsyncMock()
        session.flush = AsyncMock()
        session_factory.return_value.__aenter__.return_value = session

        alert = MagicMock()
        alert.ticker = "IMOEX"
        alert.timeframe.value = "1D"
        alert.type.value = "volume_spike"
        alert.direction.value = "bullish"
        alert.severity.value = "warning"
        alert.score = 0.85
        alert.message = "test"
        alert.as_of = None

        mock_result = MagicMock()
        mock_result.alerts = (alert,)
        analyze_uc.execute.return_value = mock_result

        mock_exec_result = MagicMock()
        mock_exec_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_exec_result)

        await persist_alerts(
            analyze_uc=analyze_uc,
            session_factory=session_factory,
        )

        assert analyze_uc.execute.call_count == 2


class TestEvaluateForecasts:
    async def test_evaluates_pending_forecasts(self) -> None:
        forecast_service = AsyncMock()
        quote_service = AsyncMock()
        quote = MagicMock()
        quote.last = Decimal("110.00")
        quote_service.get_quote = AsyncMock(return_value=quote)

        forecast = MagicMock()
        forecast.id = 1
        forecast.ticker = "SBER"
        forecast.bullish_probability = 0.7
        forecast.bearish_probability = 0.2
        forecast_service.find_ready_for_evaluation = AsyncMock(return_value=[forecast])

        await evaluate_forecasts(
            forecast_service=forecast_service,
            quote_service=quote_service,
        )

        forecast_service.evaluate_forecast.assert_awaited_once()

    async def test_skips_when_no_pending(self) -> None:
        forecast_service = AsyncMock()
        quote_service = AsyncMock()
        forecast_service.find_ready_for_evaluation = AsyncMock(return_value=[])

        await evaluate_forecasts(
            forecast_service=forecast_service,
            quote_service=quote_service,
        )

        forecast_service.evaluate_forecast.assert_not_awaited()
