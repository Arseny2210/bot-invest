"""Unit tests for the individual alert rules (one rule per concern)."""

from __future__ import annotations

from decimal import Decimal

from moex_analyst.domain.alerts.enums import AlertDirection, AlertSeverity, AlertType
from moex_analyst.domain.alerts.rules import (
    rule_ema20_cross_ema50,
    rule_market_structure_change,
    rule_resistance_breakout,
    rule_rsi_overbought,
    rule_rsi_oversold,
    rule_strong_bearish_signal,
    rule_strong_bullish_signal,
    rule_support_breakdown,
    rule_trend_change,
    rule_volume_spike,
)
from moex_analyst.domain.analysis.enums import (
    LevelKind,
    StructurePoint,
    TrendDirection,
    TrendStrength,
    VolumeCondition,
)
from moex_analyst.domain.analysis.result import (
    IndicatorSnapshot,
    ProbabilityDistribution,
    StructureState,
    TrendState,
)
from tests.unit.alerts.conftest import make_level, make_result


class TestSupportBreakdown:
    def test_fires_when_price_below_support(self) -> None:
        result = make_result(
            indicators=IndicatorSnapshot(ema20=Decimal("90")),
            support_levels=(make_level(LevelKind.SUPPORT, 100.0, strength=0.8),),
        )
        alert = rule_support_breakdown(result)
        assert alert is not None
        assert alert.type is AlertType.SUPPORT_BREAKDOWN
        assert alert.direction is AlertDirection.BEARISH
        assert alert.severity is AlertSeverity.CRITICAL  # strength 0.8 >= 0.70

    def test_silent_when_price_above_support(self) -> None:
        result = make_result(
            indicators=IndicatorSnapshot(ema20=Decimal("110")),
            support_levels=(make_level(LevelKind.SUPPORT, 100.0),),
        )
        assert rule_support_breakdown(result) is None

    def test_silent_without_reference_price(self) -> None:
        result = make_result(
            indicators=IndicatorSnapshot(ema20=None),
            support_levels=(make_level(LevelKind.SUPPORT, 100.0),),
        )
        assert rule_support_breakdown(result) is None

    def test_weak_level_yields_info_severity(self) -> None:
        result = make_result(
            indicators=IndicatorSnapshot(ema20=Decimal("90")),
            support_levels=(make_level(LevelKind.SUPPORT, 100.0, strength=0.2),),
        )
        alert = rule_support_breakdown(result)
        assert alert is not None
        assert alert.severity is AlertSeverity.INFO  # strength 0.2 < 0.40

    def test_picks_strongest_broken_support(self) -> None:
        result = make_result(
            indicators=IndicatorSnapshot(ema20=Decimal("80")),
            support_levels=(
                make_level(LevelKind.SUPPORT, 100.0, strength=0.3),
                make_level(LevelKind.SUPPORT, 90.0, strength=0.9),
            ),
        )
        alert = rule_support_breakdown(result)
        assert alert is not None
        assert alert.score == 0.9


class TestResistanceBreakout:
    def test_fires_when_price_above_resistance(self) -> None:
        result = make_result(
            indicators=IndicatorSnapshot(ema20=Decimal("110")),
            resistance_levels=(make_level(LevelKind.RESISTANCE, 100.0, strength=0.5),),
        )
        alert = rule_resistance_breakout(result)
        assert alert is not None
        assert alert.type is AlertType.RESISTANCE_BREAKOUT
        assert alert.direction is AlertDirection.BULLISH
        assert alert.severity is AlertSeverity.WARNING  # 0.40 <= 0.5 < 0.70

    def test_silent_when_price_below_resistance(self) -> None:
        result = make_result(
            indicators=IndicatorSnapshot(ema20=Decimal("90")),
            resistance_levels=(make_level(LevelKind.RESISTANCE, 100.0),),
        )
        assert rule_resistance_breakout(result) is None


class TestTrendChange:
    def test_uptrend_with_bearish_structure_fires(self) -> None:
        result = make_result(
            trend=TrendState(
                direction=TrendDirection.UP, strength=TrendStrength.WEAK, score=0.3,
            ),
            structure=StructureState(
                swings=(), last_high=StructurePoint.LH, last_low=StructurePoint.LL,
            ),
        )
        alert = rule_trend_change(result)
        assert alert is not None
        assert alert.type is AlertType.TREND_CHANGE
        assert alert.direction is AlertDirection.BEARISH

    def test_downtrend_with_bullish_structure_fires(self) -> None:
        result = make_result(
            trend=TrendState(
                direction=TrendDirection.DOWN, strength=TrendStrength.WEAK, score=-0.3,
            ),
            structure=StructureState(
                swings=(), last_high=StructurePoint.HH, last_low=StructurePoint.HL,
            ),
        )
        alert = rule_trend_change(result)
        assert alert is not None
        assert alert.direction is AlertDirection.BULLISH

    def test_aligned_trend_and_structure_silent(self) -> None:
        result = make_result(
            trend=TrendState(
                direction=TrendDirection.UP, strength=TrendStrength.STRONG, score=0.7,
            ),
            structure=StructureState(
                swings=(), last_high=StructurePoint.HH, last_low=StructurePoint.HL,
            ),
        )
        assert rule_trend_change(result) is None


class TestMarketStructureChange:
    def test_bullish_structure_confirmed(self) -> None:
        result = make_result(
            structure=StructureState(
                swings=(), last_high=StructurePoint.HH, last_low=StructurePoint.HL,
            ),
        )
        alert = rule_market_structure_change(result)
        assert alert is not None
        assert alert.direction is AlertDirection.BULLISH

    def test_bearish_structure_confirmed(self) -> None:
        result = make_result(
            structure=StructureState(
                swings=(), last_high=StructurePoint.LH, last_low=StructurePoint.LL,
            ),
        )
        alert = rule_market_structure_change(result)
        assert alert is not None
        assert alert.direction is AlertDirection.BEARISH

    def test_mixed_structure_silent(self) -> None:
        result = make_result(
            structure=StructureState(
                swings=(), last_high=StructurePoint.HH, last_low=StructurePoint.LL,
            ),
        )
        assert rule_market_structure_change(result) is None


class TestEmaCross:
    def test_bullish_stack(self) -> None:
        result = make_result(
            indicators=IndicatorSnapshot(ema20=Decimal("105"), ema50=Decimal("100")),
        )
        alert = rule_ema20_cross_ema50(result)
        assert alert is not None
        assert alert.direction is AlertDirection.BULLISH

    def test_bearish_stack(self) -> None:
        result = make_result(
            indicators=IndicatorSnapshot(ema20=Decimal("95"), ema50=Decimal("100")),
        )
        alert = rule_ema20_cross_ema50(result)
        assert alert is not None
        assert alert.direction is AlertDirection.BEARISH

    def test_equal_emas_silent(self) -> None:
        result = make_result(
            indicators=IndicatorSnapshot(ema20=Decimal("100"), ema50=Decimal("100")),
        )
        assert rule_ema20_cross_ema50(result) is None

    def test_missing_ema_silent(self) -> None:
        result = make_result(
            indicators=IndicatorSnapshot(ema20=Decimal("100"), ema50=None),
        )
        assert rule_ema20_cross_ema50(result) is None


class TestRsi:
    def test_overbought_fires_at_threshold(self) -> None:
        result = make_result(indicators=IndicatorSnapshot(rsi14=Decimal("70")))
        alert = rule_rsi_overbought(result)
        assert alert is not None
        assert alert.type is AlertType.RSI_OVERBOUGHT
        assert alert.direction is AlertDirection.BEARISH

    def test_overbought_silent_below_threshold(self) -> None:
        result = make_result(indicators=IndicatorSnapshot(rsi14=Decimal("69.99")))
        assert rule_rsi_overbought(result) is None

    def test_oversold_fires_at_threshold(self) -> None:
        result = make_result(indicators=IndicatorSnapshot(rsi14=Decimal("30")))
        alert = rule_rsi_oversold(result)
        assert alert is not None
        assert alert.direction is AlertDirection.BULLISH

    def test_oversold_silent_above_threshold(self) -> None:
        result = make_result(indicators=IndicatorSnapshot(rsi14=Decimal("30.01")))
        assert rule_rsi_oversold(result) is None

    def test_rsi_none_silent(self) -> None:
        result = make_result(indicators=IndicatorSnapshot(rsi14=None))
        assert rule_rsi_overbought(result) is None
        assert rule_rsi_oversold(result) is None


class TestVolumeSpike:
    def test_high_volume_fires(self) -> None:
        result = make_result(volume_condition=VolumeCondition.HIGH)
        alert = rule_volume_spike(result)
        assert alert is not None
        assert alert.direction is AlertDirection.NEUTRAL

    def test_normal_volume_silent(self) -> None:
        for cond in (VolumeCondition.NORMAL, VolumeCondition.LOW, VolumeCondition.UNKNOWN):
            assert rule_volume_spike(make_result(volume_condition=cond)) is None


class TestStrongSignals:
    def test_strong_bullish_fires(self) -> None:
        result = make_result(
            trend=TrendState(
                direction=TrendDirection.UP, strength=TrendStrength.STRONG, score=0.8,
            ),
            probabilities=ProbabilityDistribution(
                bullish=0.6, bearish=0.2, sideways=0.2,
            ),
        )
        alert = rule_strong_bullish_signal(result)
        assert alert is not None
        assert alert.severity is AlertSeverity.CRITICAL
        assert alert.score == 0.6

    def test_strong_bullish_silent_when_weak(self) -> None:
        result = make_result(
            trend=TrendState(
                direction=TrendDirection.UP, strength=TrendStrength.WEAK, score=0.3,
            ),
            probabilities=ProbabilityDistribution(
                bullish=0.6, bearish=0.2, sideways=0.2,
            ),
        )
        assert rule_strong_bullish_signal(result) is None

    def test_strong_bearish_fires(self) -> None:
        result = make_result(
            trend=TrendState(
                direction=TrendDirection.DOWN, strength=TrendStrength.STRONG, score=-0.8,
            ),
            probabilities=ProbabilityDistribution(
                bullish=0.2, bearish=0.6, sideways=0.2,
            ),
        )
        alert = rule_strong_bearish_signal(result)
        assert alert is not None
        assert alert.severity is AlertSeverity.CRITICAL

    def test_strong_bearish_silent_for_uptrend(self) -> None:
        result = make_result(
            trend=TrendState(
                direction=TrendDirection.UP, strength=TrendStrength.STRONG, score=0.8,
            ),
            probabilities=ProbabilityDistribution(
                bullish=0.6, bearish=0.2, sideways=0.2,
            ),
        )
        assert rule_strong_bearish_signal(result) is None
