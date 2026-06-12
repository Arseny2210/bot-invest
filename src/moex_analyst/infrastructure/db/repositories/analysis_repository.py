"""Repository for :class:`AnalysisRecord`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from moex_analyst.infrastructure.db.models import AnalysisRecord
from moex_analyst.infrastructure.db.repositories.base import BaseRepository

if TYPE_CHECKING:
    from datetime import datetime

__all__ = ["AnalysisRepository"]


class AnalysisRepository(BaseRepository[AnalysisRecord]):
    model = AnalysisRecord

    async def find_by_ticker(
        self,
        ticker: str,
        *,
        limit: int = 100,
    ) -> list[AnalysisRecord]:
        stmt = (
            select(AnalysisRecord)
            .where(AnalysisRecord.ticker == ticker)
            .order_by(AnalysisRecord.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_since(
        self,
        since: datetime,
        *,
        ticker: str | None = None,
    ) -> list[AnalysisRecord]:
        stmt = select(AnalysisRecord).where(AnalysisRecord.created_at >= since)
        if ticker is not None:
            stmt = stmt.where(AnalysisRecord.ticker == ticker)
        stmt = stmt.order_by(AnalysisRecord.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
