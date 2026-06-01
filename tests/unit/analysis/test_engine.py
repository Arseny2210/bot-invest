"""Unit tests for the AnalysisEngine orchestrator (CandleSeriesDTO -> result)."""

from __future__ import annotations

import pytest

from moex_analyst.domain.analysis import (
    AnalysisEngine,
    InsufficientDataError,
    TrendDirection,
)
from moex_analyst.domain.analysis.enums import VolumeCondition
from moex_analyst.domain.market.timeframe import Timeframe
from tests.unit.analysis.conftest import series_from_closes


class TestEngineContract:
    def test_raises_on_insufficient_data(self) -> None:
        engine = AnalysisEngine()
        series = series_from_closes([100.0] * 10)  # < MIN_CANDLES
        with pytest.raises(InsufficientDataError) as exc:
            engine.analyse(series)
        assert exc.value.required == 15
        assert exc.value.got == 10

    def test_result_carries_ticker_and_timeframe(self) -> None:
        engine = AnalysisEngine()
        series = series_from_closes(
            [100.0 + i for i in range(60)], ticker="SNGS", timeframe=Timeframe.D1,
        )
        result = engine.analyse(series)
        assert result.ticker == "SNGS"
        assert result.timeframe is Timeframe.D1
        assert result.candles_analysed == 60
        assert result.as_of == series.candles[-1].begin

    def test_probabilities_sum_to_one(self) -> None:
        engine = AnalysisEngine()
        result = engine.analyse(series_from_closes([100.0 + i for i in range(60)]))
        p = result.probabilities
        assert abs(p.bullish + p.bearish + p.sideways - 1.0) < 1e-9

    def test_all_required_fields_present(self) -> None:
        engine = AnalysisEngine()
        result = engine.analyse(series_from_closes([100.0 + (i % 7) for i in range(60)]))
        # Every contracted output field exists and is populated.
        assert result.trend is not None
        assert result.structure is not None
        assert isinstance(result.support_levels, tuple)
        assert isinstance(result.resistance_levels, tuple)
        assert isinstance(result.volume_condition, VolumeCondition)
        assert result.indicators is not None
        assert result.probabilities is not None


class TestEngineBehaviour:
    @pytest.mark.parametrize("timeframe", list(Timeframe))
    def test_supports_all_timeframes(self, timeframe: Timeframe) -> None:
        engine = AnalysisEngine()
        series = series_from_closes(
            [100.0 + i for i in range(60)], timeframe=timeframe,
        )
        result = engine.analyse(series)
        assert result.timeframe is timeframe

    def test_uptrend_classified_up(self) -> None:
        engine = AnalysisEngine()
        result = engine.analyse(series_from_closes([100.0 + i for i in range(60)]))
        assert result.trend.direction is TrendDirection.UP
        assert result.probabilities.bullish > result.probabilities.bearish

    def test_indicators_populated_with_enough_history(self) -> None:
        engine = AnalysisEngine()
        result = engine.analyse(series_from_closes([100.0 + (i % 5) for i in range(60)]))
        ind = result.indicators
        assert ind.rsi14 is not None
        assert ind.atr14 is not None
        assert ind.ema20 is not None
        assert ind.ema50 is not None  # 60 candles >= 50

    def test_ema50_none_with_short_history(self) -> None:
        engine = AnalysisEngine()
        # 30 candles: EMA20 available, EMA50 not.
        result = engine.analyse(series_from_closes([100.0 + (i % 5) for i in range(30)]))
        assert result.indicators.ema20 is not None
        assert result.indicators.ema50 is None

    def test_index_zero_volume_is_unknown(self) -> None:
        engine = AnalysisEngine()
        result = engine.analyse(
            series_from_closes([100.0 + i for i in range(60)], volume=0),
        )
        assert result.volume_condition is VolumeCondition.UNKNOWN

    def test_full_determinism(self) -> None:
        engine = AnalysisEngine()
        closes = [100.0 + (i % 11) - 5 for i in range(80)]
        r1 = engine.analyse(series_from_closes(closes))
        r2 = engine.analyse(series_from_closes(closes))
        assert r1 == r2
