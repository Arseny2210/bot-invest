"""Repository for :class:`AlertRecord`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from moex_analyst.infrastructure.db.models import AlertRecord
from moex_analyst.infrastructure.db.repositories.base import BaseRepository

if TYPE_CHECKING:
    from datetime import datetime

__all__ = ["AlertRepository"]


class AlertRepository(BaseRepository[AlertRecord]):
    model = AlertRecord

    async def find_by_ticker(
        self,
        ticker: str,
        *,
        limit: int = 100,
    ) -> list[AlertRecord]:
        stmt = (
            select(AlertRecord)
            .where(AlertRecord.ticker == ticker)
            .order_by(AlertRecord.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_since(
        self,
        since: datetime,
    ) -> list[AlertRecord]:
        stmt = (
            select(AlertRecord)
            .where(AlertRecord.created_at >= since)
            .order_by(AlertRecord.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
