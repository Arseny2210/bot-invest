"""Forecast tracking service — manages predictions and their outcomes.

Stores probabilistic predictions when they are made, evaluates them against
actual prices when enough time has passed, and computes aggregate accuracy
metrics for observability and future model training.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from moex_analyst.application.services.dto import ForecastMetrics
from moex_analyst.infrastructure.db.models import ForecastStatus
from moex_analyst.infrastructure.db.repositories.forecast_repository import (
    ForecastOutcomeRepository,
    ForecastRepository,
)
from moex_analyst.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork

if TYPE_CHECKING:
    from decimal import Decimal

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from moex_analyst.domain.market.timeframe import Timeframe
    from moex_analyst.infrastructure.db.models.forecast_record import (
        ForecastOutcome,
        ForecastRecord,
    )

__all__ = ["ForecastTrackingService"]


class ForecastTrackingService:
    """Application service for forecast lifecycle management."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def save_prediction(
        self,
        ticker: str,
        timeframe: Timeframe,
        price: Decimal,
        bullish_prob: float,
        bearish_prob: float,
        sideways_prob: float,
        horizon_hours: int = 24,
    ) -> ForecastRecord:
        async with SqlAlchemyUnitOfWork(self._session_factory) as uow:
            repo = ForecastRepository(uow.session)
            record = repo.model(
                ticker=ticker,
                timeframe=timeframe.value,
                prediction_time=datetime.now(UTC),
                price_at_prediction=price,
                bullish_probability=bullish_prob,
                bearish_probability=bearish_prob,
                sideways_probability=sideways_prob,
                forecast_horizon_hours=horizon_hours,
                status=ForecastStatus.PENDING,
            )
            await repo.add(record)
            await uow.commit()
            return record

    async def find_ready_for_evaluation(self) -> list[ForecastRecord]:
        async with SqlAlchemyUnitOfWork(self._session_factory) as uow:
            repo = ForecastRepository(uow.session)
            pending = await repo.find_pending_evaluation()
            now = datetime.now(UTC)
            ready = [
                f
                for f in pending
                if f.prediction_time + timedelta(hours=f.forecast_horizon_hours) <= now
            ]
            return ready

    async def evaluate_forecast(
        self,
        forecast_id: int,
        actual_price: Decimal,
        predicted_direction: str = "bullish",
    ) -> ForecastOutcome:
        async with SqlAlchemyUnitOfWork(self._session_factory) as uow:
            forecast_repo = ForecastRepository(uow.session)
            outcome_repo = ForecastOutcomeRepository(uow.session)

            forecast = await forecast_repo.get(forecast_id)
            if forecast is None:
                raise ValueError(f"Forecast {forecast_id} not found")

            price_change = float(actual_price - forecast.price_at_prediction) / float(
                forecast.price_at_prediction,
            )

            if predicted_direction == "bullish":
                success = price_change > 0
            elif predicted_direction == "bearish":
                success = price_change < 0
            else:
                success = abs(price_change) < 0.01

            result = "SUCCESS" if success else "FAILED"

            outcome = outcome_repo.model(
                forecast_id=forecast_id,
                evaluation_time=datetime.now(UTC),
                actual_price=actual_price,
                price_change_percent=price_change * 100,
                result=result,
            )
            await outcome_repo.add(outcome)

            new_status = ForecastStatus.SUCCESS if success else ForecastStatus.FAILED
            await forecast_repo.update_status(forecast_id, new_status)
            await uow.commit()
            return outcome

    async def calculate_metrics(self) -> ForecastMetrics:
        async with SqlAlchemyUnitOfWork(self._session_factory) as uow:
            forecast_repo = ForecastRepository(uow.session)
            outcome_repo = ForecastOutcomeRepository(uow.session)

            total = await forecast_repo.count()
            success_count = await forecast_repo.count_by_status(ForecastStatus.SUCCESS)
            failed_count = await forecast_repo.count_by_status(ForecastStatus.FAILED)
            avg_change = await outcome_repo.average_price_change()

            success_rate = success_count / total if total > 0 else 0.0

            return ForecastMetrics(
                total_predictions=total,
                successful_predictions=success_count,
                failed_predictions=failed_count,
                success_rate=success_rate,
                average_price_change=avg_change,
            )
