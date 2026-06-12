"""Unit tests for scenario analysis, risk/reward, confidence, horizons, conclusion."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from moex_analyst.domain.analysis.enums import (
    LevelKind,
    StructurePoint,
    TrendDirection,
    TrendStrength,
    VolumeCondition,
)
from moex_analyst.domain.analysis.result import (
    AnalysisResult,
    IndicatorSnapshot,
    PriceLevel,
    ProbabilityDistribution,
    StructureState,
    TrendState,
)
from moex_analyst.domain.analysis.scenarios import (
    COMPONENT_WEIGHTS,
    SCENARIO_SKIP_MISSING_LEVELS,
    SCENARIO_SKIP_MISSING_PRICE,
    SCENARIO_SKIP_MISSING_RESISTANCE,
    SCENARIO_SKIP_MISSING_SUPPORT,
    build_scenarios,
    compute_conclusion,
    compute_confidence,
    compute_confidence_breakdown,
    compute_horizons,
    compute_indicator_notes,
    compute_reasoning,
    compute_risk_reward,
    compute_scenarios,
)
from moex_analyst.domain.market.timeframe import Timeframe

_AS_OF = datetime(2024, 6, 1, 15, 30, tzinfo=UTC)


def _num(formatted: str | None) -> Decimal:
    """Parse a thousands-separated formatted price back into a Decimal."""
    assert formatted is not None
    return Decimal(formatted.replace(",", ""))


def _result(
    *,
    direction: TrendDirection = TrendDirection.UP,
    strength: TrendStrength = TrendStrength.STRONG,
    score: float = 0.72,
    bullish: float = 0.6,
    bearish: float = 0.25,
    sideways: float = 0.15,
    last_high: StructurePoint | None = StructurePoint.HH,
    last_low: StructurePoint | None = StructurePoint.HL,
    volume: VolumeCondition = VolumeCondition.HIGH,
    rsi14: Decimal | None = Decimal("72.00"),
    atr14: Decimal | None = Decimal("0.5400"),
    ema20: Decimal | None = Decimal("26.1200"),
    ema50: Decimal | None = Decimal("25.4000"),
    support_price: Decimal | None = Decimal("24.50"),
    resistance_price: Decimal | None = Decimal("28.10"),
    candles_analysed: int = 120,
) -> AnalysisResult:
    supports = (
        (PriceLevel(kind=LevelKind.SUPPORT, price=support_price, touches=3, strength=0.8),)
        if support_price is not None
        else ()
    )
    resistances = (
        (PriceLevel(kind=LevelKind.RESISTANCE, price=resistance_price, touches=2, strength=0.6),)
        if resistance_price is not None
        else ()
    )
    return AnalysisResult(
        ticker="SNGS",
        timeframe=Timeframe.D1,
        as_of=_AS_OF,
        candles_analysed=candles_analysed,
        trend=TrendState(direction=direction, strength=strength, score=score),
        structure=StructureState(swings=(), last_high=last_high, last_low=last_low),
        support_levels=supports,
        resistance_levels=resistances,
        volume_condition=volume,
        indicators=IndicatorSnapshot(rsi14=rsi14, atr14=atr14, ema20=ema20, ema50=ema50),
        probabilities=ProbabilityDistribution(bullish=bullish, bearish=bearish, sideways=sideways),
    )


# ---------------------------------------------------------------------------
# compute_scenarios
# ---------------------------------------------------------------------------


class TestComputeScenarios:
    def test_bullish_scenario_with_price_and_levels(self) -> None:
        result = _result()
        scenarios = compute_scenarios(result, Decimal("26.40"))
        bull = scenarios["bullish"]
        assert bull["trigger"] is not None
        assert bull["target_1"] is not None
        assert bull["target_2"] is not None
        assert bull["invalidation"] is not None

    def test_bearish_scenario_with_price_and_levels(self) -> None:
        result = _result()
        scenarios = compute_scenarios(result, Decimal("26.40"))
        bear = scenarios["bearish"]
        assert bear["trigger"] is not None
        assert bear["target_1"] is not None
        assert bear["target_2"] is not None
        assert bear["invalidation"] is not None

    def test_no_price_returns_none_triggers(self) -> None:
        result = _result()
        scenarios = compute_scenarios(result, None)
        for side in ("bullish", "bearish"):
            for k in ("trigger", "target_1", "target_2", "invalidation"):
                assert scenarios[side][k] is None

    def test_no_levels_returns_none_triggers(self) -> None:
        result = _result(support_price=None, resistance_price=None)
        scenarios = compute_scenarios(result, Decimal("26.40"))
        for side in ("bullish", "bearish"):
            for k in ("trigger", "target_1", "target_2", "invalidation"):
                assert scenarios[side][k] is None

    def test_targets_use_atr_when_available(self) -> None:
        result = _result(atr14=Decimal("1.00"))
        scenarios = compute_scenarios(result, Decimal("26.40"))
        bull = scenarios["bullish"]
        assert bull["target_1"] == "29.10"  # resistance 28.10 + ATR 1.00
        assert bull["target_2"] == "30.10"  # resistance 28.10 + ATR 2.00

    def test_fallback_targets_without_atr(self) -> None:
        result = _result(atr14=None)
        scenarios = compute_scenarios(result, Decimal("26.40"))
        bull = scenarios["bullish"]
        assert bull["target_1"] is not None
        assert bull["target_2"] is not None

    def test_deterministic(self) -> None:
        result = _result()
        a = compute_scenarios(result, Decimal("26.40"))
        b = compute_scenarios(result, Decimal("26.40"))
        assert a == b

    def test_bullish_fallback_when_price_above_resistance(self) -> None:
        # No resistance overhead, but an uptrend + support below → the bullish
        # side falls back to a trend continuation anchored at the price.
        result = _result(direction=TrendDirection.UP)
        scenarios = compute_scenarios(result, Decimal("30.00"))
        assert scenarios["bullish"]["trigger"] == "30.00"
        # A support still sits below → bearish breakdown remains valid too.
        assert scenarios["bearish"]["trigger"] is not None

    def test_bearish_fallback_when_price_below_support(self) -> None:
        # No support below, but a downtrend + resistance above → bearish falls
        # back to a continuation anchored at the price.
        result = _result(direction=TrendDirection.DOWN)
        scenarios = compute_scenarios(result, Decimal("20.00"))
        assert scenarios["bearish"]["trigger"] == "20.00"
        assert scenarios["bullish"]["trigger"] is not None

    def test_no_fallback_against_trend(self) -> None:
        # Price above resistance with a *down* trend → no bullish fallback (we
        # don't invent a long against the trend); bearish breakdown still holds.
        result = _result(direction=TrendDirection.DOWN)
        scenarios = compute_scenarios(result, Decimal("30.00"))
        assert scenarios["bullish"]["trigger"] is None
        assert scenarios["bearish"]["trigger"] is not None

    def test_targets_ordered_and_invalidation_consistent(self) -> None:
        result = _result()
        bull = compute_scenarios(result, Decimal("26.40"))["bullish"]
        trigger = _num(bull["trigger"])
        assert _num(bull["target_1"]) > trigger
        assert _num(bull["target_2"]) > _num(bull["target_1"])
        assert _num(bull["invalidation"]) < trigger

        bear = compute_scenarios(result, Decimal("26.40"))["bearish"]
        b_trigger = _num(bear["trigger"])
        assert _num(bear["target_1"]) < b_trigger
        assert _num(bear["target_2"]) < _num(bear["target_1"])
        assert _num(bear["invalidation"]) > b_trigger


# ---------------------------------------------------------------------------
# build_scenarios (diagnostics + fallback)
# ---------------------------------------------------------------------------


class TestBuildScenarios:
    def test_normal_case_has_setup_no_reasons(self) -> None:
        outcome = build_scenarios(_result(), Decimal("26.40"))
        assert outcome.has_setup is True
        assert outcome.skip_reasons == ()

    def test_missing_price_reason(self) -> None:
        outcome = build_scenarios(_result(), None)
        assert outcome.has_setup is False
        assert outcome.skip_reasons == (SCENARIO_SKIP_MISSING_PRICE,)

    def test_missing_levels_reason(self) -> None:
        result = _result(support_price=None, resistance_price=None)
        outcome = build_scenarios(result, Decimal("26.40"))
        assert outcome.has_setup is False
        assert outcome.skip_reasons == (SCENARIO_SKIP_MISSING_LEVELS,)

    def test_inverted_levels_yield_no_setup_with_reasons(self) -> None:
        # Support sits *above* the price and resistance *below* it: neither a
        # breakout nor a fallback is possible → no setup, both reasons logged.
        result = _result(support_price=Decimal("28.00"), resistance_price=Decimal("24.00"))
        outcome = build_scenarios(result, Decimal("26.40"))
        assert outcome.has_setup is False
        assert SCENARIO_SKIP_MISSING_RESISTANCE in outcome.skip_reasons
        assert SCENARIO_SKIP_MISSING_SUPPORT in outcome.skip_reasons

    def test_fallback_builds_setup_above_resistance(self) -> None:
        result = _result(direction=TrendDirection.UP)
        outcome = build_scenarios(result, Decimal("30.00"))
        assert outcome.has_setup is True

    def test_compute_scenarios_matches_build(self) -> None:
        result = _result()
        outcome = build_scenarios(result, Decimal("26.40"))
        assert compute_scenarios(result, Decimal("26.40")) == {
            "bullish": outcome.bullish,
            "bearish": outcome.bearish,
        }


# ---------------------------------------------------------------------------
# compute_risk_reward
# ---------------------------------------------------------------------------


class TestComputeRiskReward:
    def test_returns_all_fields(self) -> None:
        result = _result()
        rr = compute_risk_reward(result, Decimal("26.40"))
        assert rr["entry"] is not None
        assert rr["side"] in ("bullish", "bearish")

    def test_bullish_side(self) -> None:
        result = _result(bullish=0.8, bearish=0.1, sideways=0.1)
        rr = compute_risk_reward(result, Decimal("26.40"))
        assert rr["side"] == "bullish"

    def test_bearish_side(self) -> None:
        result = _result(bullish=0.1, bearish=0.8, sideways=0.1)
        rr = compute_risk_reward(result, Decimal("26.40"))
        assert rr["side"] == "bearish"

    def test_no_price_returns_none(self) -> None:
        result = _result()
        rr = compute_risk_reward(result, None)
        assert rr["entry"] is None
        assert rr["side"] is None

    def test_ratio_is_normalised_to_one(self) -> None:
        result = _result()
        rr = compute_risk_reward(result, Decimal("26.40"))
        ratio = rr["ratio"]
        if ratio is not None:
            left, right = ratio.split(":")
            assert left == "1"
            assert float(right) > 0  # "1:2.5" → reward per unit of risk

    def test_stop_below_entry_for_bullish(self) -> None:
        result = _result(bullish=0.8, bearish=0.1, sideways=0.1)
        rr = compute_risk_reward(result, Decimal("26.40"))
        assert Decimal(rr["stop_loss"].replace(",", "")) < Decimal("26.40")
        assert Decimal(rr["target"].replace(",", "")) > Decimal("26.40")

    def test_stop_above_entry_for_bearish(self) -> None:
        result = _result(bullish=0.1, bearish=0.8, sideways=0.1)
        rr = compute_risk_reward(result, Decimal("26.40"))
        assert Decimal(rr["stop_loss"].replace(",", "")) > Decimal("26.40")
        assert Decimal(rr["target"].replace(",", "")) < Decimal("26.40")

    def test_deterministic(self) -> None:
        result = _result()
        a = compute_risk_reward(result, Decimal("26.40"))
        b = compute_risk_reward(result, Decimal("26.40"))
        assert a == b


# ---------------------------------------------------------------------------
# compute_confidence
# ---------------------------------------------------------------------------


class TestComputeConfidence:
    def test_returns_in_range(self) -> None:
        result = _result()
        score = compute_confidence(result)
        assert 0 <= score <= 100

    def test_strong_uptrend_gives_high_score(self) -> None:
        result = _result(
            direction=TrendDirection.UP,
            strength=TrendStrength.STRONG,
            score=0.9,
            volume=VolumeCondition.HIGH,
            last_high=StructurePoint.HH,
            last_low=StructurePoint.HL,
        )
        score = compute_confidence(result)
        assert score >= 50

    def test_weak_sideways_gives_low_score(self) -> None:
        result = _result(
            direction=TrendDirection.SIDEWAYS,
            strength=TrendStrength.NONE,
            score=0.0,
            volume=VolumeCondition.LOW,
            last_high=None,
            last_low=None,
        )
        score = compute_confidence(result)
        assert score < 50

    def test_deterministic(self) -> None:
        result = _result()
        a = compute_confidence(result)
        b = compute_confidence(result)
        assert a == b


# ---------------------------------------------------------------------------
# compute_confidence_breakdown
# ---------------------------------------------------------------------------


class TestConfidenceBreakdown:
    def test_contains_all_components(self) -> None:
        result = _result()
        bd = compute_confidence_breakdown(result)
        for key in (*COMPONENT_WEIGHTS, "total"):
            assert key in bd

    def test_total_matches_compute_confidence(self) -> None:
        result = _result()
        assert round(compute_confidence_breakdown(result)["total"]) == compute_confidence(result)

    def test_components_in_unit_interval(self) -> None:
        result = _result()
        bd = compute_confidence_breakdown(result)
        for key in COMPONENT_WEIGHTS:
            assert 0.0 <= bd[key] <= 100.0


# ---------------------------------------------------------------------------
# compute_conclusion
# ---------------------------------------------------------------------------


class TestConclusion:
    def test_bullish_conclusion(self) -> None:
        result = _result(bullish=0.8, bearish=0.15, sideways=0.05)
        text = compute_conclusion(result, Decimal("26.40"))
        assert "рост" in text.lower() or "бычий" in text.lower()

    def test_bearish_conclusion(self) -> None:
        result = _result(bullish=0.15, bearish=0.8, sideways=0.05)
        text = compute_conclusion(result, Decimal("26.40"))
        assert "снижение" in text.lower() or "медвежий" in text.lower()

    def test_sideways_conclusion(self) -> None:
        result = _result(bullish=0.2, bearish=0.2, sideways=0.6)
        text = compute_conclusion(result, Decimal("26.40"))
        assert "консолидируется" in text.lower()

    def test_deterministic(self) -> None:
        result = _result()
        a = compute_conclusion(result, Decimal("26.40"))
        b = compute_conclusion(result, Decimal("26.40"))
        assert a == b


# ---------------------------------------------------------------------------
# compute_horizons
# ---------------------------------------------------------------------------


class TestHorizons:
    def test_contains_all_horizons(self) -> None:
        result = _result()
        h = compute_horizons(result)
        for key in ("24h", "48h", "7d"):
            assert key in h

    def test_each_horizon_sums_to_one(self) -> None:
        result = _result()
        h = compute_horizons(result)
        for key in ("24h", "48h", "7d"):
            total = h[key]["bullish"] + h[key]["bearish"] + h[key]["sideways"]
            assert abs(total - 1.0) < 0.001

    def test_24h_matches_base(self) -> None:
        result = _result(bullish=0.6, bearish=0.3, sideways=0.1)
        h = compute_horizons(result)
        assert h["24h"]["bullish"] == pytest.approx(0.6)
        assert h["24h"]["bearish"] == pytest.approx(0.3)
        assert h["24h"]["sideways"] == pytest.approx(0.1)

    def test_longer_horizon_moves_toward_uniform(self) -> None:
        result = _result(bullish=0.9, bearish=0.05, sideways=0.05)
        h = compute_horizons(result)
        # 24h is close to base
        assert h["24h"]["bullish"] == pytest.approx(0.9)
        # 7d is closer to uniform (1/3) than 24h is
        dist_24h = abs(h["24h"]["bullish"] - 1.0 / 3.0)
        dist_7d = abs(h["7d"]["bullish"] - 1.0 / 3.0)
        assert dist_7d < dist_24h

    def test_48h_blend_exact_values(self) -> None:
        # 48h blends 70% base + 30% uniform(1/3): 0.6*0.7 + 0.1 = 0.52, etc.
        result = _result(bullish=0.6, bearish=0.3, sideways=0.1)
        h = compute_horizons(result)
        assert h["48h"]["bullish"] == pytest.approx(0.52)
        assert h["48h"]["bearish"] == pytest.approx(0.31)
        assert h["48h"]["sideways"] == pytest.approx(0.17)

    def test_7d_blend_exact_values(self) -> None:
        # 7d blends 40% base + 60% uniform(1/3): 0.6*0.4 + 0.2 = 0.44, etc.
        result = _result(bullish=0.6, bearish=0.3, sideways=0.1)
        h = compute_horizons(result)
        assert h["7d"]["bullish"] == pytest.approx(0.44)
        assert h["7d"]["bearish"] == pytest.approx(0.32)
        assert h["7d"]["sideways"] == pytest.approx(0.24)

    def test_deterministic(self) -> None:
        result = _result()
        a = compute_horizons(result)
        b = compute_horizons(result)
        assert a == b


# ---------------------------------------------------------------------------
# COMPONENT_WEIGHTS
# ---------------------------------------------------------------------------


class TestComponentWeights:
    def test_sum_to_one(self) -> None:
        assert abs(sum(COMPONENT_WEIGHTS.values()) - 1.0) < 1e-9

    def test_all_positive(self) -> None:
        for w in COMPONENT_WEIGHTS.values():
            assert w > 0


# ---------------------------------------------------------------------------
# compute_indicator_notes
# ---------------------------------------------------------------------------


class TestIndicatorNotes:
    def test_all_keys_present(self) -> None:
        notes = compute_indicator_notes(_result(), Decimal("26.40"))
        assert set(notes) == {"rsi", "ema20", "ema50", "atr14"}

    def test_rsi_overbought(self) -> None:
        notes = compute_indicator_notes(_result(rsi14=Decimal("72")), Decimal("26.40"))
        assert notes["rsi"] == "перекупленность"

    def test_rsi_oversold(self) -> None:
        notes = compute_indicator_notes(_result(rsi14=Decimal("25")), Decimal("26.40"))
        assert notes["rsi"] == "перепроданность"

    def test_rsi_neutral(self) -> None:
        notes = compute_indicator_notes(_result(rsi14=Decimal("50")), Decimal("26.40"))
        assert notes["rsi"] == "нейтральная зона"

    def test_ema20_relative_to_price(self) -> None:
        result = _result(ema20=Decimal("26.00"))
        assert compute_indicator_notes(result, Decimal("26.40"))["ema20"] == "цена выше"
        assert compute_indicator_notes(result, Decimal("25.00"))["ema20"] == "цена ниже"

    def test_missing_values_yield_none(self) -> None:
        result = _result(rsi14=None, ema20=None, ema50=None, atr14=None)
        notes = compute_indicator_notes(result, Decimal("26.40"))
        assert all(v is None for v in notes.values())

    def test_no_price_skips_price_relative_notes(self) -> None:
        notes = compute_indicator_notes(_result(), None)
        assert notes["ema20"] is None
        assert notes["atr14"] is None
        # EMA20 vs EMA50 does not need the price.
        assert notes["ema50"] is not None


# ---------------------------------------------------------------------------
# compute_reasoning
# ---------------------------------------------------------------------------


class TestReasoning:
    def test_returns_non_empty_bullets(self) -> None:
        reasons = compute_reasoning(_result(), Decimal("26.40"))
        assert len(reasons) >= 3
        assert all(isinstance(r, str) and r for r in reasons)

    def test_mentions_dominant_outcome(self) -> None:
        reasons = compute_reasoning(
            _result(bullish=0.8, bearish=0.15, sideways=0.05), Decimal("26.40")
        )
        joined = " ".join(reasons).lower()
        assert "рост" in joined
        assert "80%" in " ".join(reasons)

    def test_deterministic(self) -> None:
        result = _result()
        assert compute_reasoning(result, Decimal("26.40")) == compute_reasoning(
            result, Decimal("26.40")
        )
