"""Unit tests for the AlertDetector orchestrator (AnalysisResult -> alerts)."""

from __future__ import annotations

from decimal import Decimal

from moex_analyst.domain.alerts import AlertDetector, AlertType
from moex_analyst.domain.alerts.rules import DEFAULT_RULES
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


def _strong_bull_result():
    """A snapshot that trips several bullish rules at once."""
    return make_result(
        trend=TrendState(
            direction=TrendDirection.UP, strength=TrendStrength.STRONG, score=0.8,
        ),
        structure=StructureState(
            swings=(), last_high=StructurePoint.HH, last_low=StructurePoint.HL,
        ),
        resistance_levels=(make_level(LevelKind.RESISTANCE, 100.0, strength=0.6),),
        volume_condition=VolumeCondition.HIGH,
        indicators=IndicatorSnapshot(
            rsi14=Decimal("72"), ema20=Decimal("110"), ema50=Decimal("100"),
        ),
        probabilities=ProbabilityDistribution(bullish=0.7, bearish=0.1, sideways=0.2),
    )


class TestDetectorContract:
    def test_quiet_result_yields_no_alerts(self) -> None:
        assert AlertDetector().detect(make_result()) == []

    def test_returns_list_of_alerts(self) -> None:
        alerts = AlertDetector().detect(_strong_bull_result())
        assert isinstance(alerts, list)
        assert len(alerts) >= 1

    def test_provenance_copied_onto_every_alert(self) -> None:
        result = _strong_bull_result()
        for alert in AlertDetector().detect(result):
            assert alert.ticker == result.ticker
            assert alert.timeframe is result.timeframe
            assert alert.as_of == result.as_of

    def test_output_ordering_follows_rule_order(self) -> None:
        alerts = AlertDetector().detect(_strong_bull_result())
        types = [a.type for a in alerts]
        # Resistance breakout precedes the strong-bullish composite by rule order.
        assert types.index(AlertType.RESISTANCE_BREAKOUT) < types.index(
            AlertType.STRONG_BULLISH_SIGNAL,
        )


class TestDetectorBehaviour:
    def test_strong_bull_trips_expected_alert_set(self) -> None:
        alerts = AlertDetector().detect(_strong_bull_result())
        fired = {a.type for a in alerts}
        assert {
            AlertType.RESISTANCE_BREAKOUT,
            AlertType.EMA20_CROSS_EMA50,
            AlertType.RSI_OVERBOUGHT,
            AlertType.VOLUME_SPIKE,
            AlertType.MARKET_STRUCTURE_CHANGE,
            AlertType.STRONG_BULLISH_SIGNAL,
        } <= fired

    def test_deterministic_repeated_calls(self) -> None:
        result = _strong_bull_result()
        detector = AlertDetector()
        assert detector.detect(result) == detector.detect(result)

    def test_idempotent_across_instances(self) -> None:
        result = _strong_bull_result()
        assert AlertDetector().detect(result) == AlertDetector().detect(result)

    def test_custom_rule_subset_is_respected(self) -> None:
        detector = AlertDetector(rules=[DEFAULT_RULES[4]])  # rsi_overbought only
        alerts = detector.detect(_strong_bull_result())
        assert [a.type for a in alerts] == [AlertType.RSI_OVERBOUGHT]

    def test_empty_rule_set_yields_no_alerts(self) -> None:
        assert AlertDetector(rules=[]).detect(_strong_bull_result()) == []


class TestDetectReport:
    def test_report_carries_provenance_and_alerts(self) -> None:
        result = _strong_bull_result()
        report = AlertDetector().detect_report(result)
        assert report.ticker == result.ticker
        assert report.timeframe is result.timeframe
        assert report.as_of == result.as_of
        assert not report.is_empty
        assert tuple(report.alerts) == tuple(AlertDetector().detect(result))

    def test_empty_report_for_quiet_result(self) -> None:
        report = AlertDetector().detect_report(make_result())
        assert report.is_empty
        assert report.highest_severity is None
