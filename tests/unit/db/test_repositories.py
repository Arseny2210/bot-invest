"""Tests for repository query methods — each test mocks the async session."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from moex_analyst.infrastructure.db.models import (
    AlertRecord,
    AnalysisRecord,
    ForecastOutcome,
    ForecastRecord,
)
from moex_analyst.infrastructure.db.repositories.alert_repository import (
    AlertRepository,
)
from moex_analyst.infrastructure.db.repositories.analysis_repository import (
    AnalysisRepository,
)
from moex_analyst.infrastructure.db.repositories.forecast_repository import (
    ForecastOutcomeRepository,
    ForecastRepository,
)


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock()


class TestAnalysisRepository:
    async def test_find_by_ticker(self, mock_session: AsyncMock) -> None:
        repo = AnalysisRepository(mock_session)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            MagicMock(spec=AnalysisRecord),
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.find_by_ticker("SBER")

        assert len(result) == 1

    async def test_find_since(self, mock_session: AsyncMock) -> None:
        repo = AnalysisRepository(mock_session)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.find_since(datetime(2025, 1, 1, tzinfo=UTC))

        assert result == []


class TestAlertRepository:
    async def test_find_by_ticker(self, mock_session: AsyncMock) -> None:
        repo = AlertRepository(mock_session)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            MagicMock(spec=AlertRecord),
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.find_by_ticker("SBER")

        assert len(result) == 1

    async def test_find_since(self, mock_session: AsyncMock) -> None:
        repo = AlertRepository(mock_session)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.find_since(datetime(2025, 1, 1, tzinfo=UTC))

        assert result == []


class TestForecastRepository:
    async def test_find_pending_evaluation(self, mock_session: AsyncMock) -> None:
        repo = ForecastRepository(mock_session)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            MagicMock(spec=ForecastRecord),
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.find_pending_evaluation()

        assert len(result) == 1

    async def test_update_status(self, mock_session: AsyncMock) -> None:
        repo = ForecastRepository(mock_session)
        mock_session.execute = AsyncMock()

        await repo.update_status(1, "SUCCESS")

        assert mock_session.execute.await_count == 1
        assert mock_session.flush.await_count == 1

    async def test_count_by_status(self, mock_session: AsyncMock) -> None:
        repo = ForecastRepository(mock_session)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [MagicMock(), MagicMock()]
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.count_by_status("SUCCESS")

        assert result == 2

    async def test_add_creates_record(self, mock_session: AsyncMock) -> None:
        repo = ForecastRepository(mock_session)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        record = ForecastRecord(
            ticker="SBER",
            timeframe="1D",
            prediction_time=datetime(2025, 6, 1, 12, tzinfo=UTC),
            price_at_prediction=Decimal("250.00"),
            bullish_probability=0.7,
            bearish_probability=0.1,
            sideways_probability=0.2,
            forecast_horizon_hours=24,
            status="PENDING",
        )
        added = await repo.add(record)

        mock_session.add.assert_called_once_with(record)
        assert added == record


class TestForecastOutcomeRepository:
    async def test_find_by_forecast(self, mock_session: AsyncMock) -> None:
        repo = ForecastOutcomeRepository(mock_session)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            MagicMock(spec=ForecastOutcome),
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.find_by_forecast(1)

        assert len(result) == 1

    async def test_average_price_change(self, mock_session: AsyncMock) -> None:
        repo = ForecastOutcomeRepository(mock_session)
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 2.5
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.average_price_change()

        assert result == 2.5
