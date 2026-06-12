"""Analysis persistence model — stores every analysis engine output.

Maps an :class:`moex_analyst.domain.analysis.AnalysisResult` into a flat
relational row for future ML dataset collection.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Float, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from moex_analyst.infrastructure.db.base import Base, TimestampMixin

__all__ = ["AnalysisRecord"]


class AnalysisRecord(Base, TimestampMixin):
    __tablename__ = "analysis_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    timeframe: Mapped[str] = mapped_column(String(4), nullable=False)

    as_of: Mapped[datetime] = mapped_column(nullable=False)

    trend_direction: Mapped[str] = mapped_column(String(16), nullable=False)
    trend_strength: Mapped[str] = mapped_column(String(16), nullable=False)
    trend_score: Mapped[float] = mapped_column(Float, nullable=False)

    bullish_probability: Mapped[float] = mapped_column(Float, nullable=False)
    bearish_probability: Mapped[float] = mapped_column(Float, nullable=False)
    sideways_probability: Mapped[float] = mapped_column(Float, nullable=False)

    rsi: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    atr: Mapped[Decimal | None] = mapped_column(Numeric(16, 6), nullable=True)
    ema20: Mapped[Decimal | None] = mapped_column(Numeric(16, 6), nullable=True)
    ema50: Mapped[Decimal | None] = mapped_column(Numeric(16, 6), nullable=True)

    support_levels: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    resistance_levels: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    volume_state: Mapped[str] = mapped_column(String(16), nullable=False)

    market_structure: Mapped[str] = mapped_column(Text, nullable=False, default="")

    candles_analysed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
