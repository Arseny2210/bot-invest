"""Deterministic alert rules over an :class:`AnalysisResult`.

Each rule is a pure function ``(AnalysisResult) -> Alert | None``: it inspects
the analysis snapshot and either raises exactly one alert of its type or returns
``None``. Rules never read clocks, randomness, files, the network or any other
ambient state — given the same :class:`AnalysisResult` they always return the
same alert (deterministic and idempotent).

Reference price
---------------
``AnalysisResult`` does not carry the raw last close (the analysis layer exposes
only smoothed/indicator values). EMA20 is therefore used as the *reference
price* for level-relative rules (support breakdown / resistance breakout). It is
the indicator that tracks the latest bar most closely; when it is unavailable
(too little history) the price-relative rules simply do not fire.

Snapshot semantics
------------------
``*_CROSS_*`` / ``*_CHANGE`` alerts describe a *condition currently present* in
the snapshot (e.g. EMA20 sits above EMA50), not a tick-by-tick transition — the
snapshot carries last values, not the full series. A stateful caller turns these
level-triggered conditions into edge-triggered notifications via
:attr:`Alert.dedup_key`; that concern is deliberately outside this pure engine.
"""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from moex_analyst.domain.alerts.dto import Alert
from moex_analyst.domain.alerts.enums import AlertDirection, AlertSeverity, AlertType
from moex_analyst.domain.analysis.enums import (
    StructurePoint,
    TrendDirection,
    TrendStrength,
    VolumeCondition,
)
from moex_analyst.domain.analysis.result import AnalysisResult, PriceLevel

__all__ = [
    "DEFAULT_RULES",
    "Rule",
    "rule_ema20_cross_ema50",
    "rule_market_structure_change",
    "rule_resistance_breakout",
    "rule_rsi_overbought",
    "rule_rsi_oversold",
    "rule_strong_bearish_signal",
    "rule_strong_bullish_signal",
    "rule_support_breakdown",
    "rule_trend_change",
    "rule_volume_spike",
]

Rule = Callable[[AnalysisResult], "Alert | None"]

# --- thresholds (module-level so they are explicit and test-visible) --------
RSI_OVERBOUGHT = Decimal("70")
RSI_OVERSOLD = Decimal("30")
# Bullish-momentum RSI band used as a confirmation in the composite signals.
RSI_BULL_MIN = Decimal("50")
RSI_BEAR_MAX = Decimal("50")

# Probability dominance required for a STRONG composite signal.
STRONG_PROB = 0.45

# PriceLevel.strength bands -> severity for level-relative alerts.
LEVEL_CRITICAL = 0.70
LEVEL_WARNING = 0.40


# --- shared helpers ---------------------------------------------------------
def _alert(
    result: AnalysisResult,
    *,
    type_: AlertType,
    direction: AlertDirection,
    severity: AlertSeverity,
    score: float,
    message: str,
) -> Alert:
    """Build an :class:`Alert`, copying provenance from the source result."""
    return Alert(
        type=type_,
        direction=direction,
        severity=severity,
        score=max(0.0, min(1.0, score)),
        message=message,
        ticker=result.ticker,
        timeframe=result.timeframe,
        as_of=result.as_of,
    )


def _reference_price(result: AnalysisResult) -> float | None:
    """Best available proxy for the latest price (EMA20), or ``None``."""
    ema20 = result.indicators.ema20
    return float(ema20) if ema20 is not None else None


def _severity_from_strength(strength: float) -> AlertSeverity:
    if strength >= LEVEL_CRITICAL:
        return AlertSeverity.CRITICAL
    if strength >= LEVEL_WARNING:
        return AlertSeverity.WARNING
    return AlertSeverity.INFO


def _is_bullish_structure(result: AnalysisResult) -> bool:
    s = result.structure
    return s.last_high is StructurePoint.HH or s.last_low is StructurePoint.HL


def _is_bearish_structure(result: AnalysisResult) -> bool:
    s = result.structure
    return s.last_high is StructurePoint.LH or s.last_low is StructurePoint.LL


# --- level-relative rules ---------------------------------------------------
def rule_support_breakdown(result: AnalysisResult) -> Alert | None:
    """Reference price has fallen below a support level (strongest broken one)."""
    ref = _reference_price(result)
    if ref is None:
        return None
    broken = [lvl for lvl in result.support_levels if ref < float(lvl.price)]
    if not broken:
        return None
    level = _strongest(broken)
    return _alert(
        result,
        type_=AlertType.SUPPORT_BREAKDOWN,
        direction=AlertDirection.BEARISH,
        severity=_severity_from_strength(level.strength),
        score=level.strength,
        message=(
            f"Цена {ref:g} пробила поддержку {float(level.price):g} "
            f"({level.touches} касаний, надёжность {level.strength:.2f})"
        ),
    )


def rule_resistance_breakout(result: AnalysisResult) -> Alert | None:
    """Reference price has risen above a resistance level (strongest broken one)."""
    ref = _reference_price(result)
    if ref is None:
        return None
    broken = [lvl for lvl in result.resistance_levels if ref > float(lvl.price)]
    if not broken:
        return None
    level = _strongest(broken)
    return _alert(
        result,
        type_=AlertType.RESISTANCE_BREAKOUT,
        direction=AlertDirection.BULLISH,
        severity=_severity_from_strength(level.strength),
        score=level.strength,
        message=(
            f"Цена {ref:g} пробила сопротивление {float(level.price):g} "
            f"({level.touches} касаний, надёжность {level.strength:.2f})"
        ),
    )


def _strongest(levels: list[PriceLevel]) -> PriceLevel:
    return max(levels, key=lambda lvl: lvl.strength)


# --- structure / trend rules ------------------------------------------------
def rule_trend_change(result: AnalysisResult) -> Alert | None:
    """Trend direction and market structure disagree — early trend-change warning.

    Fires when the prevailing trend is up but structure has turned bearish (or
    vice versa) and the structure is unambiguously one-sided.
    """
    trend = result.trend
    bullish = _is_bullish_structure(result)
    bearish = _is_bearish_structure(result)

    if trend.direction is TrendDirection.UP and bearish and not bullish:
        return _alert(
            result,
            type_=AlertType.TREND_CHANGE,
            direction=AlertDirection.BEARISH,
            severity=AlertSeverity.WARNING,
            score=min(1.0, abs(trend.score) + 0.25),
            message="Восходящий тренд теряет структуру: последние свинги развернулись вниз",
        )
    if trend.direction is TrendDirection.DOWN and bullish and not bearish:
        return _alert(
            result,
            type_=AlertType.TREND_CHANGE,
            direction=AlertDirection.BULLISH,
            severity=AlertSeverity.WARNING,
            score=min(1.0, abs(trend.score) + 0.25),
            message="Нисходящий тренд теряет структуру: последние свинги развернулись вверх",
        )
    return None


def rule_market_structure_change(result: AnalysisResult) -> Alert | None:
    """An unambiguous bullish (HH+HL) or bearish (LH+LL) structure is in place."""
    s = result.structure
    if s.last_high is StructurePoint.HH and s.last_low is StructurePoint.HL:
        return _alert(
            result,
            type_=AlertType.MARKET_STRUCTURE_CHANGE,
            direction=AlertDirection.BULLISH,
            severity=AlertSeverity.INFO,
            score=0.6,
            message="Бычья рыночная структура подтверждена (higher high + higher low)",
        )
    if s.last_high is StructurePoint.LH and s.last_low is StructurePoint.LL:
        return _alert(
            result,
            type_=AlertType.MARKET_STRUCTURE_CHANGE,
            direction=AlertDirection.BEARISH,
            severity=AlertSeverity.INFO,
            score=0.6,
            message="Медвежья рыночная структура подтверждена (lower high + lower low)",
        )
    return None


# --- indicator rules --------------------------------------------------------
def rule_ema20_cross_ema50(result: AnalysisResult) -> Alert | None:
    """EMA20 sits clearly on one side of EMA50 (golden vs death-cross state)."""
    ema20 = result.indicators.ema20
    ema50 = result.indicators.ema50
    if ema20 is None or ema50 is None or ema20 == ema50:
        return None
    if ema20 > ema50:
        direction = AlertDirection.BULLISH
        message = f"EMA20 {float(ema20):g} выше EMA50 {float(ema50):g} (бычий стек)"
    else:
        direction = AlertDirection.BEARISH
        message = f"EMA20 {float(ema20):g} ниже EMA50 {float(ema50):g} (медвежий стек)"
    return _alert(
        result,
        type_=AlertType.EMA20_CROSS_EMA50,
        direction=direction,
        severity=AlertSeverity.INFO,
        score=0.5,
        message=message,
    )


def rule_rsi_overbought(result: AnalysisResult) -> Alert | None:
    rsi = result.indicators.rsi14
    if rsi is None or rsi < RSI_OVERBOUGHT:
        return None
    return _alert(
        result,
        type_=AlertType.RSI_OVERBOUGHT,
        direction=AlertDirection.BEARISH,
        severity=AlertSeverity.WARNING,
        score=float(min(rsi, Decimal("100")) / Decimal("100")),
        message=f"RSI14 {float(rsi):g} перекуплен (>= {float(RSI_OVERBOUGHT):g})",
    )


def rule_rsi_oversold(result: AnalysisResult) -> Alert | None:
    rsi = result.indicators.rsi14
    if rsi is None or rsi > RSI_OVERSOLD:
        return None
    return _alert(
        result,
        type_=AlertType.RSI_OVERSOLD,
        direction=AlertDirection.BULLISH,
        severity=AlertSeverity.WARNING,
        score=float((Decimal("100") - max(rsi, Decimal("0"))) / Decimal("100")),
        message=f"RSI14 {float(rsi):g} перепродан (<= {float(RSI_OVERSOLD):g})",
    )


def rule_volume_spike(result: AnalysisResult) -> Alert | None:
    """Current volume regime is elevated relative to its recent average."""
    if result.volume_condition is not VolumeCondition.HIGH:
        return None
    return _alert(
        result,
        type_=AlertType.VOLUME_SPIKE,
        direction=AlertDirection.NEUTRAL,
        severity=AlertSeverity.WARNING,
        score=0.7,
        message="Всплеск объёма: текущий объём значительно выше среднего",
    )


# --- composite (confluence) rules -------------------------------------------
def rule_strong_bullish_signal(result: AnalysisResult) -> Alert | None:
    """Strong up-trend with dominant bullish probability."""
    trend = result.trend
    probs = result.probabilities
    if (
        trend.direction is TrendDirection.UP
        and trend.strength is TrendStrength.STRONG
        and probs.bullish >= STRONG_PROB
        and probs.bullish >= probs.bearish
    ):
        return _alert(
            result,
            type_=AlertType.STRONG_BULLISH_SIGNAL,
            direction=AlertDirection.BULLISH,
            severity=AlertSeverity.CRITICAL,
            score=probs.bullish,
            message=(
                f"Сильный бычий сигнал: восходящий тренд (оценка {trend.score:.2f}) "
                f"с вероятностью роста {probs.bullish:.2f}"
            ),
        )
    return None


def rule_strong_bearish_signal(result: AnalysisResult) -> Alert | None:
    """Strong down-trend with dominant bearish probability."""
    trend = result.trend
    probs = result.probabilities
    if (
        trend.direction is TrendDirection.DOWN
        and trend.strength is TrendStrength.STRONG
        and probs.bearish >= STRONG_PROB
        and probs.bearish >= probs.bullish
    ):
        return _alert(
            result,
            type_=AlertType.STRONG_BEARISH_SIGNAL,
            direction=AlertDirection.BEARISH,
            severity=AlertSeverity.CRITICAL,
            score=probs.bearish,
            message=(
                f"Сильный медвежий сигнал: нисходящий тренд (оценка {trend.score:.2f}) "
                f"с вероятностью снижения {probs.bearish:.2f}"
            ),
        )
    return None


# Fixed evaluation order -> deterministic alert ordering in the output list.
# Mirrors the canonical alert-type ordering of the spec.
DEFAULT_RULES: tuple[Rule, ...] = (
    rule_support_breakdown,
    rule_resistance_breakout,
    rule_trend_change,
    rule_ema20_cross_ema50,
    rule_rsi_overbought,
    rule_rsi_oversold,
    rule_volume_spike,
    rule_market_structure_change,
    rule_strong_bullish_signal,
    rule_strong_bearish_signal,
)
