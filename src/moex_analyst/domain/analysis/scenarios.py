"""Scenario analysis, risk/reward, confidence score, and prediction horizons.

All functions are deterministic pure computations over an :class:`AnalysisResult`
and an optional current price. No AI, no randomness, no I/O.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, NamedTuple

from moex_analyst.domain.analysis.enums import (
    StructurePoint,
    TrendDirection,
    TrendStrength,
    VolumeCondition,
)

if TYPE_CHECKING:
    from moex_analyst.domain.analysis import AnalysisResult, TrendState

__all__ = [
    "COMPONENT_WEIGHTS",
    "SCENARIO_SKIP_INVALID_TARGETS",
    "SCENARIO_SKIP_MISSING_LEVELS",
    "SCENARIO_SKIP_MISSING_PRICE",
    "SCENARIO_SKIP_MISSING_RESISTANCE",
    "SCENARIO_SKIP_MISSING_SUPPORT",
    "ScenarioOutcome",
    "build_scenarios",
    "compute_conclusion",
    "compute_confidence",
    "compute_confidence_breakdown",
    "compute_horizons",
    "compute_indicator_notes",
    "compute_reasoning",
    "compute_risk_reward",
    "compute_scenarios",
]


# ---------------------------------------------------------------------------
# Level selection
# ---------------------------------------------------------------------------


def _nearest_resistance_above(analysis: AnalysisResult, price: Decimal) -> Decimal | None:
    """The closest resistance strictly above ``price`` (the breakout level)."""
    above = [lvl.price for lvl in analysis.resistance_levels if lvl.price > price]
    return min(above) if above else None


def _nearest_support_below(analysis: AnalysisResult, price: Decimal) -> Decimal | None:
    """The closest support strictly below ``price`` (the breakdown level)."""
    below = [lvl.price for lvl in analysis.support_levels if lvl.price < price]
    return max(below) if below else None


# ---------------------------------------------------------------------------
# Scenario levels
# ---------------------------------------------------------------------------


# Reason codes recorded when a scenario side cannot be generated. They are
# surfaced to the presentation layer purely for logging — never shown to users.
SCENARIO_SKIP_MISSING_PRICE = "missing_price"
SCENARIO_SKIP_MISSING_LEVELS = "missing_levels"
SCENARIO_SKIP_MISSING_RESISTANCE = "missing_resistance_level"
SCENARIO_SKIP_MISSING_SUPPORT = "missing_support_level"
SCENARIO_SKIP_INVALID_TARGETS = "invalid_targets"

_EMPTY_SIDE: dict[str, str | None] = {
    "trigger": None,
    "target_1": None,
    "target_2": None,
    "invalidation": None,
}


class ScenarioOutcome(NamedTuple):
    """Generated scenarios plus diagnostics for the caller to log.

    ``skip_reasons`` collects machine-readable reason codes (see the
    ``SCENARIO_SKIP_*`` constants) for every side that could not be built.
    """

    bullish: dict[str, str | None]
    bearish: dict[str, str | None]
    skip_reasons: tuple[str, ...]

    @property
    def has_setup(self) -> bool:
        """True when at least one side produced a usable trade setup."""
        return bool(self.bullish["trigger"] or self.bearish["trigger"])


def build_scenarios(
    analysis: AnalysisResult,
    current_price: Decimal | None,
    decimals: int = 2,
) -> ScenarioOutcome:
    """Generate bullish/bearish scenarios with a trend-aware fallback.

    Per side, generation is attempted in order:

    1. **Breakout** through the nearest level beyond price — resistance above
       for the bullish side, support below for the bearish side.
    2. **Fallback continuation** along the trend, anchored at the current price
       and sized from the opposite level, when no breakout level is overhead.

    A side is only left empty — and a reason code recorded — when neither path
    is possible (no price, no levels at all, an unbuildable side, or targets
    that fail the consistency guard).
    """
    if current_price is None:
        return ScenarioOutcome(dict(_EMPTY_SIDE), dict(_EMPTY_SIDE), (SCENARIO_SKIP_MISSING_PRICE,))

    if not analysis.support_levels and not analysis.resistance_levels:
        return ScenarioOutcome(
            dict(_EMPTY_SIDE), dict(_EMPTY_SIDE), (SCENARIO_SKIP_MISSING_LEVELS,)
        )

    price = current_price
    atr = Decimal(str(analysis.indicators.atr14)) if analysis.indicators.atr14 is not None else None
    resistance = _nearest_resistance_above(analysis, price)
    support = _nearest_support_below(analysis, price)

    reasons: list[str] = []
    bullish = _bullish_side(price, resistance, support, atr, analysis.trend, decimals, reasons)
    bearish = _bearish_side(price, support, resistance, atr, analysis.trend, decimals, reasons)
    return ScenarioOutcome(bullish, bearish, tuple(reasons))


def compute_scenarios(
    analysis: AnalysisResult,
    current_price: Decimal | None,
    decimals: int = 2,
) -> dict[str, dict[str, str | None]]:
    """Backwards-compatible view of :func:`build_scenarios` (sides only)."""
    outcome = build_scenarios(analysis, current_price, decimals)
    return {"bullish": outcome.bullish, "bearish": outcome.bearish}


def _bullish_side(
    price: Decimal,
    resistance: Decimal | None,
    support: Decimal | None,
    atr: Decimal | None,
    trend: TrendState,
    decimals: int,
    reasons: list[str],
) -> dict[str, str | None]:
    if resistance is not None:
        # Preferred: break up through the nearest resistance overhead.
        trigger = resistance
        step = atr if atr is not None and atr > 0 else trigger * Decimal("0.05")
        invalidation = support if support is not None else price * Decimal("0.97")
    elif trend.direction is not TrendDirection.DOWN and support is not None:
        # Fallback: no overhead resistance — ride the trend up from price,
        # sized off the nearest support below.
        trigger = price
        step = atr if atr is not None and atr > 0 else price - support
        invalidation = support
    else:
        reasons.append(SCENARIO_SKIP_MISSING_RESISTANCE)
        return dict(_EMPTY_SIDE)

    target_1 = trigger + step
    target_2 = trigger + step * Decimal("2")
    if not (step > 0 and target_1 > trigger < target_2 and invalidation < trigger):
        reasons.append(SCENARIO_SKIP_INVALID_TARGETS)
        return dict(_EMPTY_SIDE)
    return {
        "trigger": _fmt(trigger, decimals),
        "target_1": _fmt(target_1, decimals),
        "target_2": _fmt(target_2, decimals),
        "invalidation": _fmt(invalidation, decimals),
    }


def _bearish_side(
    price: Decimal,
    support: Decimal | None,
    resistance: Decimal | None,
    atr: Decimal | None,
    trend: TrendState,
    decimals: int,
    reasons: list[str],
) -> dict[str, str | None]:
    if support is not None:
        # Preferred: break down through the nearest support below.
        trigger = support
        step = atr if atr is not None and atr > 0 else trigger * Decimal("0.05")
        invalidation = resistance if resistance is not None else price * Decimal("1.03")
    elif trend.direction is not TrendDirection.UP and resistance is not None:
        # Fallback: no support below — ride the trend down from price, sized
        # off the nearest resistance above.
        trigger = price
        step = atr if atr is not None and atr > 0 else resistance - price
        invalidation = resistance
    else:
        reasons.append(SCENARIO_SKIP_MISSING_SUPPORT)
        return dict(_EMPTY_SIDE)

    target_1 = trigger - step
    target_2 = trigger - step * Decimal("2")
    if not (step > 0 and target_1 < trigger > target_2 and invalidation > trigger):
        reasons.append(SCENARIO_SKIP_INVALID_TARGETS)
        return dict(_EMPTY_SIDE)
    return {
        "trigger": _fmt(trigger, decimals),
        "target_1": _fmt(target_1, decimals),
        "target_2": _fmt(target_2, decimals),
        "invalidation": _fmt(invalidation, decimals),
    }


# ---------------------------------------------------------------------------
# Risk / Reward
# ---------------------------------------------------------------------------


def compute_risk_reward(
    analysis: AnalysisResult,
    current_price: Decimal | None,
    decimals: int = 2,
) -> dict[str, str | None]:
    """Calculate entry, stop-loss, target and risk/reward ratio.

    Uses the dominant directional scenario and validates that the stop sits on
    the losing side of the entry and the target on the winning side. The ratio
    is normalised to ``"1:R"`` (one unit of risk to ``R`` units of reward) and
    is ``None`` whenever the geometry is degenerate (non-positive risk or
    reward), so the report never shows a misleading number.

    Returns::
        {
            "entry": ...,
            "stop_loss": ...,
            "target": ...,
            "ratio": "1:R" | None,
            "side": "bullish" | "bearish",
        }
    """
    price = current_price
    probs = analysis.probabilities

    if price is None:
        return {"entry": None, "stop_loss": None, "target": None, "ratio": None, "side": None}

    atr = Decimal(str(analysis.indicators.atr14)) if analysis.indicators.atr14 is not None else None
    resistance = _nearest_resistance_above(analysis, price)
    support = _nearest_support_below(analysis, price)

    entry = price
    if probs.bullish >= probs.bearish:
        side = "bullish"
        stop = support
        if stop is not None and resistance is not None:
            target = resistance + (resistance - stop) * Decimal("0.5")
        elif resistance is not None:
            target = resistance * Decimal("1.03")
        else:
            target = entry + atr if atr is not None else entry * Decimal("1.03")
    else:
        side = "bearish"
        stop = resistance
        if stop is not None and support is not None:
            target = support - (stop - support) * Decimal("0.5")
        elif support is not None:
            target = support * Decimal("0.97")
        else:
            target = entry - atr if atr is not None else entry * Decimal("0.97")

    sl = stop if stop is not None else _default_stop(price, side, atr)
    # Validate the stop is on the losing side; fall back to an ATR/percent stop.
    if (side == "bullish" and sl >= entry) or (side == "bearish" and sl <= entry):
        sl = _default_stop(price, side, atr)

    if side == "bullish":
        risk, reward = entry - sl, target - entry
    else:
        risk, reward = sl - entry, entry - target

    ratio = f"1:{(reward / risk):.1f}" if risk > 0 and reward > 0 else None

    return {
        "entry": _fmt(entry, decimals),
        "stop_loss": _fmt(sl, decimals),
        "target": _fmt(target, decimals),
        "ratio": ratio,
        "side": side,
    }


def _default_stop(price: Decimal, side: str, atr: Decimal | None) -> Decimal:
    if atr is None:
        return price * Decimal("0.97") if side == "bullish" else price * Decimal("1.03")
    return price - Decimal(str(atr)) if side == "bullish" else price + Decimal(str(atr))


# ---------------------------------------------------------------------------
# Confidence score  (0-100)
# ---------------------------------------------------------------------------

# Component weights used to blend the final confidence score.
COMPONENT_WEIGHTS: dict[str, float] = {
    "trend": 0.30,
    "structure": 0.25,
    "volume": 0.15,
    "volatility": 0.10,
    "probability": 0.20,
}


def _confidence_components(analysis: AnalysisResult) -> dict[str, float]:
    """Compute individual component scores (0-100 each).

    Returns:
        ``{"trend": …, "structure": …, "volume": …, "volatility": …, "probability": …}``
    """
    trend = analysis.trend
    structure = analysis.structure
    probs = analysis.probabilities

    # --- Trend alignment (0-100) ---
    trend_raw = abs(trend.score) * 100.0
    match trend.strength:
        case _ if trend.strength.value == "strong":
            trend_score = trend_raw
        case _ if trend.strength.value == "weak":
            trend_score = trend_raw * 0.7
        case _:
            trend_score = trend_raw * 0.3
    trend_score = min(100.0, trend_score)

    # --- Structure alignment (0-100) ---
    is_up = trend.direction is TrendDirection.UP
    is_down = trend.direction is TrendDirection.DOWN
    hh = structure.last_high is StructurePoint.HH
    hl = structure.last_low is StructurePoint.HL
    lh = structure.last_high is StructurePoint.LH
    ll = structure.last_low is StructurePoint.LL

    if is_up and hh and hl:
        struct_score = 90.0
    elif is_up and (hh or hl):
        struct_score = 60.0
    elif is_down and lh and ll:
        struct_score = 90.0
    elif is_down and (lh or ll):
        struct_score = 60.0
    elif trend.direction is TrendDirection.SIDEWAYS:
        struct_score = 50.0
    else:
        struct_score = 30.0

    # --- Volume confirmation (0-100) ---
    match analysis.volume_condition:
        case VolumeCondition.HIGH:
            volume_score: float = 80.0
        case VolumeCondition.NORMAL:
            volume_score = 50.0
        case VolumeCondition.LOW:
            volume_score = 30.0
        case VolumeCondition.UNKNOWN:
            volume_score = 50.0

    # --- Volatility (0-100) ---
    atr = analysis.indicators.atr14
    if atr is not None and analysis.candles_analysed > 0:
        price = _estimate_price(analysis)
        if price and price > 0:
            atr_pct = float(atr) / float(price)
            volatility_score: float = max(0.0, min(100.0, 100.0 - atr_pct * 1000.0))
        else:
            volatility_score = 60.0
    else:
        volatility_score = 60.0

    # --- Probability dominance (0-100) ---
    max_prob = max(probs.bullish, probs.bearish)
    prob_score = 40.0 if probs.sideways >= max_prob else (max_prob - 0.33) / 0.67 * 100.0
    prob_score = min(100.0, max(0.0, prob_score))

    return {
        "trend": trend_score,
        "structure": struct_score,
        "volume": volume_score,
        "volatility": volatility_score,
        "probability": prob_score,
    }


def compute_confidence_breakdown(analysis: AnalysisResult) -> dict[str, float]:
    """Compute a full confidence breakdown with individual component scores.

    Returns a dict like::

        {
            "trend": 72.0,
            "structure": 90.0,
            "volume": 80.0,
            "volatility": 60.0,
            "probability": 60.0,
            "total": 74.9,     # weighted blend in [0, 100]
        }
    """
    components = _confidence_components(analysis)
    total = sum(components[k] * COMPONENT_WEIGHTS[k] for k in COMPONENT_WEIGHTS)
    return {**components, "total": round(total, 1)}


def compute_confidence(analysis: AnalysisResult) -> int:
    """Compute a 0-100 confidence score based on multiple factors.

    Components:
      * Trend alignment        (weight 30 %)
      * Structure alignment    (weight 25 %)
      * Volume confirmation    (weight 15 %)
      * Volatility             (weight 10 %)
      * Probability dominance  (weight 20 %)
    """
    return round(compute_confidence_breakdown(analysis)["total"])


# ---------------------------------------------------------------------------
# Conclusion
# ---------------------------------------------------------------------------


def compute_conclusion(
    analysis: AnalysisResult,
    current_price: Decimal | None,
) -> str:
    """Generate a short one-sentence conclusion based on the analysis."""
    probs = analysis.probabilities

    if probs.bullish > max(probs.bearish, probs.sideways):
        return _conclusion_bullish(analysis, current_price)
    if probs.bearish > max(probs.bullish, probs.sideways):
        return _conclusion_bearish(analysis, current_price)
    return _conclusion_sideways(analysis, current_price)


def _conclusion_bullish(analysis: AnalysisResult, price: Decimal | None) -> str:
    support = analysis.support_levels[0].price if analysis.support_levels else None
    timeframe = analysis.timeframe.value

    horizon = "24–48 часов" if timeframe in ("15M", "1H", "4H") else "2–5 дней"
    level = support if support is not None else (price * Decimal("0.97") if price else None)

    level_str = f"{float(level):.2f} ₽" if level else "текущих уровней"
    return (
        f"Наиболее вероятен рост в течение ближайших {horizon}. "
        f"Бычий сценарий остаётся актуальным выше уровня {level_str}."
    )


def _conclusion_bearish(analysis: AnalysisResult, price: Decimal | None) -> str:
    resistance = analysis.resistance_levels[0].price if analysis.resistance_levels else None
    timeframe = analysis.timeframe.value

    horizon = "24–48 часов" if timeframe in ("15M", "1H", "4H") else "2–5 дней"
    level = resistance if resistance is not None else (price * Decimal("1.03") if price else None)

    level_str = f"{float(level):.2f} ₽" if level else "текущих уровней"
    return (
        f"Наиболее вероятно снижение в течение ближайших {horizon}. "
        f"Медвежий сценарий остаётся актуальным ниже уровня {level_str}."
    )


def _conclusion_sideways(analysis: AnalysisResult, price: Decimal | None) -> str:
    support = analysis.support_levels[0].price if analysis.support_levels else None
    resistance = analysis.resistance_levels[0].price if analysis.resistance_levels else None

    if support and resistance:
        return (
            f"Рынок консолидируется между {float(support):.2f} ₽ "
            f"и {float(resistance):.2f} ₽. "
            "Ожидайте пробоя одного из уровней для входа в рынок."
        )
    return "Рынок консолидируется. Определённого направления нет."


# ---------------------------------------------------------------------------
# Indicator descriptions
# ---------------------------------------------------------------------------


def compute_indicator_notes(
    analysis: AnalysisResult,
    price: Decimal | None,
) -> dict[str, str | None]:
    """Short human-readable note per indicator (``None`` when not computable).

    Keys: ``rsi``, ``ema20``, ``ema50``, ``atr14``.
    """
    ind = analysis.indicators
    notes: dict[str, str | None] = {"rsi": None, "ema20": None, "ema50": None, "atr14": None}

    if ind.rsi14 is not None:
        if ind.rsi14 >= Decimal("70"):
            notes["rsi"] = "перекупленность"
        elif ind.rsi14 <= Decimal("30"):
            notes["rsi"] = "перепроданность"
        else:
            notes["rsi"] = "нейтральная зона"

    if ind.ema20 is not None and price is not None:
        notes["ema20"] = "цена выше" if price >= ind.ema20 else "цена ниже"

    if ind.ema20 is not None and ind.ema50 is not None:
        notes["ema50"] = "EMA20 выше EMA50" if ind.ema20 >= ind.ema50 else "EMA20 ниже EMA50"

    if ind.atr14 is not None and price is not None and price > 0:
        pct = ind.atr14 / price * Decimal("100")
        if pct < Decimal("1"):
            notes["atr14"] = "низкая волатильность"
        elif pct <= Decimal("3"):
            notes["atr14"] = "умеренная волатильность"
        else:
            notes["atr14"] = "высокая волатильность"

    return notes


# ---------------------------------------------------------------------------
# Forecast reasoning ("why")
# ---------------------------------------------------------------------------

_TREND_DIRECTION_WORDS: dict[TrendDirection, str] = {
    TrendDirection.UP: "восходящий",
    TrendDirection.DOWN: "нисходящий",
    TrendDirection.SIDEWAYS: "боковой",
}

_TREND_STRENGTH_WORDS: dict[TrendStrength, str] = {
    TrendStrength.STRONG: "сильный",
    TrendStrength.WEAK: "слабый",
    TrendStrength.NONE: "невыраженный",
}

_VOLUME_WORDS: dict[VolumeCondition, str] = {
    VolumeCondition.HIGH: "повышенный объём подтверждает движение",
    VolumeCondition.NORMAL: "объём в норме",
    VolumeCondition.LOW: "низкий объём ослабляет сигнал",
    VolumeCondition.UNKNOWN: "объём недоступен",
}


def compute_reasoning(
    analysis: AnalysisResult,
    price: Decimal | None,
) -> list[str]:
    """Explain *why* the forecast looks the way it does, as short bullet lines."""
    trend = analysis.trend
    structure = analysis.structure
    probs = analysis.probabilities
    reasons: list[str] = [
        f"Тренд {_TREND_DIRECTION_WORDS[trend.direction]}, "
        f"{_TREND_STRENGTH_WORDS[trend.strength]} (оценка {trend.score:+.2f}).",
    ]

    if structure.last_high is StructurePoint.HH and structure.last_low is StructurePoint.HL:
        reasons.append("Структура за рост: растущие максимумы и минимумы.")
    elif structure.last_high is StructurePoint.LH and structure.last_low is StructurePoint.LL:
        reasons.append("Структура за снижение: падающие максимумы и минимумы.")
    else:
        reasons.append("Структура смешанная — единого направления нет.")

    reasons.append(_VOLUME_WORDS[analysis.volume_condition].capitalize() + ".")

    rsi_note = compute_indicator_notes(analysis, price)["rsi"]
    if rsi_note is not None:
        reasons.append(f"RSI: {rsi_note}.")

    pairs = (("рост", probs.bullish), ("снижение", probs.bearish), ("боковик", probs.sideways))
    label, value = max(pairs, key=lambda p: p[1])
    reasons.append(f"Наиболее вероятен {label} — {value * 100:.0f}%.")

    return reasons


# ---------------------------------------------------------------------------
# Prediction horizons
# ---------------------------------------------------------------------------


def compute_horizons(analysis: AnalysisResult) -> dict[str, dict[str, float]]:
    """Compute probability forecasts for 24h, 48h and 7d horizons.

    Extends the base probabilities with increasing uncertainty for longer
    horizons. All probabilities sum to 1.0 within each horizon.
    """
    base = analysis.probabilities
    b, be, s = base.bullish, base.bearish, base.sideways

    def _blend(b: float, be: float, s: float, weight_base: float) -> dict[str, float]:
        weight_uniform = 1.0 - weight_base
        u = 1.0 / 3.0
        return {
            "bullish": round(b * weight_base + u * weight_uniform, 4),
            "bearish": round(be * weight_base + u * weight_uniform, 4),
            "sideways": round(s * weight_base + u * weight_uniform, 4),
        }

    return {
        "24h": _blend(b, be, s, 1.0),
        "48h": _blend(b, be, s, 0.70),
        "7d": _blend(b, be, s, 0.40),
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _fmt(value: Decimal, places: int = 2) -> str:
    """Format a Decimal to fixed places."""
    quant = Decimal(1).scaleb(-places)
    return f"{value.quantize(quant):,}"


def _estimate_price(analysis: AnalysisResult) -> Decimal | None:
    """Best-effort price estimate from available indicators."""
    ind = analysis.indicators
    if ind.ema20 is not None:
        return ind.ema20
    if ind.ema50 is not None:
        return ind.ema50
    return None
