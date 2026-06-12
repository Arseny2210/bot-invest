"""Repositories for :class:`ForecastRecord` and :class:`ForecastOutcome`."""

from __future__ import annotations

from sqlalchemy import func, select, update

from moex_analyst.infrastructure.db.models import (
    ForecastOutcome,
    ForecastRecord,
    ForecastStatus,
)
from moex_analyst.infrastructure.db.repositories.base import BaseRepository

__all__ = [
    "ForecastOutcomeRepository",
    "ForecastRepository",
]


class ForecastRepository(BaseRepository[ForecastRecord]):
    model = ForecastRecord

    async def find_pending_evaluation(
        self,
    ) -> list[ForecastRecord]:
        stmt = (
            select(ForecastRecord)
            .where(ForecastRecord.status == ForecastStatus.PENDING)
            .order_by(ForecastRecord.prediction_time.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        forecast_id: int,
        status: str,
    ) -> None:
        stmt = update(ForecastRecord).where(ForecastRecord.id == forecast_id).values(status=status)
        await self._session.execute(stmt)
        await self._session.flush()

    async def count_by_status(self, status: str) -> int:
        stmt = select(ForecastRecord).where(ForecastRecord.status == status)
        result = await self._session.execute(stmt)
        return len(result.scalars().all())


class ForecastOutcomeRepository(BaseRepository[ForecastOutcome]):
    model = ForecastOutcome

    async def find_by_forecast(
        self,
        forecast_id: int,
    ) -> list[ForecastOutcome]:
        stmt = (
            select(ForecastOutcome)
            .where(ForecastOutcome.forecast_id == forecast_id)
            .order_by(ForecastOutcome.evaluation_time.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def average_price_change(self) -> float:
        stmt = select(func.avg(ForecastOutcome.price_change_percent))
        result = await self._session.execute(stmt)
        val = result.scalar_one()
        return float(val) if val is not None else 0.0
