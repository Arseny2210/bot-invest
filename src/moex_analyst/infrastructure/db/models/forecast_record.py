"""Forecast persistence models — predictions and their actual outcomes.

:class:`ForecastRecord` stores a probabilistic prediction at a point in time.
:class:`ForecastOutcome` records what actually happened when the forecast is
evaluated.  The two-table design keeps prediction data immutable while allowing
multiple evaluation attempts (or delayed evaluation).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Float, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from moex_analyst.infrastructure.db.base import Base, TimestampMixin

__all__ = [
    "ForecastOutcome",
    "ForecastRecord",
    "ForecastStatus",
]


class ForecastStatus:
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class ForecastRecord(Base, TimestampMixin):
    __tablename__ = "forecast_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    timeframe: Mapped[str] = mapped_column(String(4), nullable=False)

    prediction_time: Mapped[datetime] = mapped_column(nullable=False)
    price_at_prediction: Mapped[Decimal] = mapped_column(Numeric(16, 6), nullable=False)

    bullish_probability: Mapped[float] = mapped_column(Float, nullable=False)
    bearish_probability: Mapped[float] = mapped_column(Float, nullable=False)
    sideways_probability: Mapped[float] = mapped_column(Float, nullable=False)

    forecast_horizon_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=ForecastStatus.PENDING,
        index=True,
    )

    outcomes: Mapped[list[ForecastOutcome]] = relationship(
        "ForecastOutcome",
        back_populates="forecast",
        cascade="all, delete-orphan",
    )


class ForecastOutcome(Base, TimestampMixin):
    __tablename__ = "forecast_outcomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    forecast_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("forecast_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    evaluation_time: Mapped[datetime] = mapped_column(nullable=False)
    actual_price: Mapped[Decimal] = mapped_column(Numeric(16, 6), nullable=False)
    price_change_percent: Mapped[float] = mapped_column(Float, nullable=False)
    result: Mapped[str] = mapped_column(String(16), nullable=False)

    forecast: Mapped[ForecastRecord] = relationship(
        "ForecastRecord",
        back_populates="outcomes",
    )
