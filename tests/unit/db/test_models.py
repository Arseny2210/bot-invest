"""Tests for the ORM model constructors — field defaults, types, and constraints."""

from datetime import UTC, datetime
from decimal import Decimal

from moex_analyst.infrastructure.db.models import (
    AlertRecord,
    AnalysisRecord,
    ForecastOutcome,
    ForecastRecord,
    ForecastStatus,
)


class TestAnalysisRecord:
    def test_minimal_construction(self) -> None:
        record = AnalysisRecord(
            ticker="SBER",
            timeframe="1D",
            as_of=datetime(2025, 6, 1, 12, tzinfo=UTC),
            trend_direction="up",
            trend_strength="strong",
            trend_score=0.5,
            bullish_probability=0.6,
            bearish_probability=0.2,
            sideways_probability=0.2,
            volume_state="normal",
            support_levels=[],
            resistance_levels=[],
            market_structure="",
            candles_analysed=0,
        )
        assert record.ticker == "SBER"
        assert record.timeframe == "1D"
        assert record.rsi is None
        assert record.support_levels == []

    def test_with_indicators(self) -> None:
        record = AnalysisRecord(
            ticker="VTBR",
            timeframe="1H",
            as_of=datetime(2025, 6, 1, 12, tzinfo=UTC),
            trend_direction="down",
            trend_strength="weak",
            trend_score=-0.3,
            bullish_probability=0.2,
            bearish_probability=0.6,
            sideways_probability=0.2,
            volume_state="high",
            support_levels=[{"kind": "support", "price": "95.0"}],
            resistance_levels=[{"kind": "resistance", "price": "105.0"}],
            market_structure="HH, HL",
            candles_analysed=120,
            rsi=Decimal("45.1234"),
            atr=Decimal("1.5"),
            ema20=Decimal("100.50"),
            ema50=Decimal("98.30"),
        )
        assert record.rsi == Decimal("45.1234")
        assert len(record.support_levels) == 1
        assert record.candles_analysed == 120


class TestAlertRecord:
    def test_minimal_construction(self) -> None:
        record = AlertRecord(
            ticker="SBER",
            timeframe="1D",
            alert_type="volume_spike",
            direction="bullish",
            severity="warning",
            score=0.85,
            message_hash="abc123",
            as_of=datetime(2025, 6, 1, 12, tzinfo=UTC),
        )
        assert record.ticker == "SBER"
        assert record.alert_type == "volume_spike"
        assert record.direction == "bullish"


class TestForecastRecord:
    def test_minimal_construction(self) -> None:
        record = ForecastRecord(
            ticker="SBER",
            timeframe="1D",
            prediction_time=datetime(2025, 6, 1, 12, tzinfo=UTC),
            price_at_prediction=Decimal("250.00"),
            bullish_probability=0.7,
            bearish_probability=0.1,
            sideways_probability=0.2,
            forecast_horizon_hours=24,
            status=ForecastStatus.PENDING,
        )
        assert record.status == ForecastStatus.PENDING
        assert record.forecast_horizon_hours == 24

    def test_with_explicit_status(self) -> None:
        record = ForecastRecord(
            ticker="VTBR",
            timeframe="1D",
            prediction_time=datetime(2025, 6, 1, 12, tzinfo=UTC),
            price_at_prediction=Decimal("100.00"),
            bullish_probability=0.3,
            bearish_probability=0.5,
            sideways_probability=0.2,
            forecast_horizon_hours=48,
            status=ForecastStatus.SUCCESS,
        )
        assert record.forecast_horizon_hours == 48
        assert record.status == ForecastStatus.SUCCESS


class TestForecastOutcome:
    def test_minimal_construction(self) -> None:
        outcome = ForecastOutcome(
            forecast_id=1,
            evaluation_time=datetime(2025, 6, 2, 12, tzinfo=UTC),
            actual_price=Decimal("260.00"),
            price_change_percent=4.0,
            result="SUCCESS",
        )
        assert outcome.forecast_id == 1
        assert outcome.price_change_percent == 4.0


class TestForecastStatus:
    def test_constants(self) -> None:
        assert ForecastStatus.PENDING == "PENDING"
        assert ForecastStatus.SUCCESS == "SUCCESS"
        assert ForecastStatus.FAILED == "FAILED"
        assert ForecastStatus.UNKNOWN == "UNKNOWN"
