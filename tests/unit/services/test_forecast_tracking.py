"""Tests for the ForecastTrackingService — mocked session and repositories."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from moex_analyst.application.services.dto import ForecastMetrics
from moex_analyst.application.services.forecast_tracking import (
    ForecastTrackingService,
)
from moex_analyst.infrastructure.db.models import ForecastStatus


@pytest.fixture
def session_factory() -> MagicMock:
    return MagicMock()


def _make_session() -> MagicMock:
    """Build a mock session compatible with SqlAlchemyUnitOfWork.

    ``BaseRepository.add`` calls ``session.add(…)`` (non-await) then
    ``await session.flush(…)``.  All other session methods are awaited, so
    ``AsyncMock`` is the natural choice — except for ``add`` / ``add_all``
    which must be plain ``MagicMock`` to avoid returning a stray coroutine.
    """
    s = AsyncMock()
    s.add = MagicMock()
    s.add_all = MagicMock()
    s.commit = AsyncMock()
    s.flush = AsyncMock()
    s.rollback = AsyncMock()
    s.close = AsyncMock()
    return s


def _configure_session_factory(
    factory: MagicMock,
    session: MagicMock | None = None,
) -> MagicMock:
    if session is None:
        session = _make_session()
    factory.return_value = session
    return session


@pytest.fixture
def service(session_factory: MagicMock) -> ForecastTrackingService:
    return ForecastTrackingService(session_factory)


class TestForecastTrackingService:
    async def test_save_prediction_creates_record(
        self,
        service: ForecastTrackingService,
        session_factory: MagicMock,
    ) -> None:
        _configure_session_factory(session_factory)

        result = await service.save_prediction(
            ticker="SBER",
            timeframe=MagicMock(value="1D"),
            price=Decimal("250.00"),
            bullish_prob=0.7,
            bearish_prob=0.2,
            sideways_prob=0.1,
        )

        assert result.ticker == "SBER"
        assert result.price_at_prediction == Decimal("250.00")
        assert result.status == ForecastStatus.PENDING

    async def test_find_ready_for_evaluation_filters_by_horizon(
        self,
        service: ForecastTrackingService,
        session_factory: MagicMock,
    ) -> None:
        session = _configure_session_factory(session_factory)

        old_record = MagicMock()
        old_record.prediction_time = datetime(2020, 1, 1, tzinfo=UTC)
        old_record.forecast_horizon_hours = 24

        new_record = MagicMock()
        new_record.prediction_time = datetime.now(UTC)
        new_record.forecast_horizon_hours = 48

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [old_record, new_record]
        session.execute = AsyncMock(return_value=mock_result)

        ready = await service.find_ready_for_evaluation()

        assert len(ready) == 1
        assert ready[0] == old_record

    async def test_evaluate_forecast_bullish_success(
        self,
        service: ForecastTrackingService,
        session_factory: MagicMock,
    ) -> None:
        session = _configure_session_factory(session_factory)

        forecast = MagicMock()
        forecast.id = 1
        forecast.price_at_prediction = Decimal("100.00")
        forecast.bullish_probability = 0.8
        forecast.bearish_probability = 0.1

        session.get = AsyncMock(return_value=forecast)
        mock_exec_result = MagicMock()
        mock_exec_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_exec_result)

        outcome = await service.evaluate_forecast(
            forecast_id=1,
            actual_price=Decimal("110.00"),
            predicted_direction="bullish",
        )

        assert outcome.result == "SUCCESS"
        assert outcome.price_change_percent == 10.0

    async def test_evaluate_forecast_bearish_success(
        self,
        service: ForecastTrackingService,
        session_factory: MagicMock,
    ) -> None:
        session = _configure_session_factory(session_factory)

        forecast = MagicMock()
        forecast.id = 1
        forecast.price_at_prediction = Decimal("100.00")
        forecast.bullish_probability = 0.3
        forecast.bearish_probability = 0.6

        session.get = AsyncMock(return_value=forecast)
        mock_exec_result = MagicMock()
        mock_exec_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_exec_result)

        outcome = await service.evaluate_forecast(
            forecast_id=1,
            actual_price=Decimal("90.00"),
            predicted_direction="bearish",
        )

        assert outcome.result == "SUCCESS"
        assert outcome.price_change_percent == -10.0

    async def test_evaluate_forecast_not_found(
        self,
        service: ForecastTrackingService,
        session_factory: MagicMock,
    ) -> None:
        _configure_session_factory(session_factory)
        session = session_factory.return_value
        session.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Forecast 1 not found"):
            await service.evaluate_forecast(
                forecast_id=1,
                actual_price=Decimal("110.00"),
            )

    async def test_calculate_metrics_empty(
        self,
        service: ForecastTrackingService,
        session_factory: MagicMock,
    ) -> None:
        session = _configure_session_factory(session_factory)

        async def mock_execute(stmt: object) -> MagicMock:
            result = MagicMock()
            result.scalar_one.return_value = 0
            result.scalars.return_value.all.return_value = []
            return result

        session.execute = mock_execute

        metrics = await service.calculate_metrics()
        assert isinstance(metrics, ForecastMetrics)
        assert metrics.total_predictions == 0
        assert metrics.success_rate == 0.0

    async def test_calculate_metrics_mixed(
        self,
        service: ForecastTrackingService,
        session_factory: MagicMock,
    ) -> None:
        """Mixed statuses: 8 success + 4 failed + 8 pending = 20 total."""
        session = _configure_session_factory(session_factory)

        call_count = 0

        async def mock_execute(stmt: object) -> MagicMock:
            nonlocal call_count
            result = MagicMock()
            call_count += 1
            if call_count == 1:
                # count() → select count(*) from forecast_records
                result.scalar_one.return_value = 20
            elif call_count in (2, 3):
                # count_by_status → select * where status = ?
                # Return a list with that many dummy items
                items = [MagicMock() for _ in (range(8) if call_count == 2 else range(4))]
                result.scalars.return_value.all.return_value = items
            elif call_count == 4:
                # average_price_change()
                result.scalar_one.return_value = 1.25
            return result

        session.execute = mock_execute

        metrics = await service.calculate_metrics()
        assert metrics.total_predictions == 20
        assert metrics.successful_predictions == 8
        assert metrics.failed_predictions == 4
        assert metrics.success_rate == 0.4
        assert metrics.average_price_change == 1.25

    async def test_calculate_metrics_all_success(
        self,
        service: ForecastTrackingService,
        session_factory: MagicMock,
    ) -> None:
        session = _configure_session_factory(session_factory)

        call_count = 0

        async def mock_execute(stmt: object) -> MagicMock:
            nonlocal call_count
            result = MagicMock()
            call_count += 1
            if call_count == 1:
                result.scalar_one.return_value = 5
            elif call_count in (2, 3):
                items = [MagicMock() for _ in range(5 if call_count == 2 else 0)]
                result.scalars.return_value.all.return_value = items
            elif call_count == 4:
                result.scalar_one.return_value = 3.5
            return result

        session.execute = mock_execute

        metrics = await service.calculate_metrics()
        assert metrics.total_predictions == 5
        assert metrics.successful_predictions == 5
        assert metrics.failed_predictions == 0
        assert metrics.success_rate == 1.0
        assert metrics.average_price_change == 3.5
