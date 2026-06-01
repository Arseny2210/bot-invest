"""Trend detection from EMA alignment, EMA slope and market structure.

Combines three independent signals into one :class:`TrendState`:
    * EMA stack: price vs EMA20 vs EMA50 (direction + alignment).
    * EMA20 slope: normalised recent slope (momentum of the fast average).
    * Structure: the latest HH/HL (up) vs LH/LL (down) labels.

A score in ``[-1, 1]`` aggregates them; its sign sets the direction and its
magnitude sets the strength band. Conflicting signals pull the score toward
zero, yielding a SIDEWAYS / NONE verdict rather than a false direction.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from moex_analyst.domain.analysis.enums import (
    StructurePoint,
    TrendDirection,
    TrendStrength,
)
from moex_analyst.domain.analysis.indicators import ema
from moex_analyst.domain.analysis.result import StructureState, TrendState

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["detect_trend"]

_STRONG = 0.5
_WEAK = 0.15


def _ema_stack_score(price: float, ema20: float | None, ema50: float | None) -> float:
    """+/- alignment of price vs EMA20 vs EMA50 in [-1, 1].

    Each comparison contributes +/-0.5; equal values contribute 0, so a flat
    market (price == EMA20 == EMA50) scores 0 rather than a false direction.
    Full bullish stack -> +1.0, full bearish stack -> -1.0.
    """
    if ema20 is None or ema50 is None:
        return 0.0
    score = 0.0
    if price > ema20:
        score += 0.5
    elif price < ema20:
        score -= 0.5
    if ema20 > ema50:
        score += 0.5
    elif ema20 < ema50:
        score -= 0.5
    return score


def _slope_score(ema20_series: Sequence[float]) -> float:
    """Normalised slope of EMA20 over its last few points, clamped to [-1, 1]."""
    if len(ema20_series) < 2:
        return 0.0
    lookback = min(5, len(ema20_series) - 1)
    start = ema20_series[-1 - lookback]
    end = ema20_series[-1]
    if start == 0.0:
        return 0.0
    rel = (end - start) / abs(start)
    # 2% move over the lookback saturates to full score.
    return max(-1.0, min(1.0, rel / 0.02))


def _structure_score(structure: StructureState) -> float:
    """+1 for up-structure (HH/HL), -1 for down-structure (LH/LL)."""
    score = 0.0
    if structure.last_high is StructurePoint.HH:
        score += 0.5
    elif structure.last_high is StructurePoint.LH:
        score -= 0.5
    if structure.last_low is StructurePoint.HL:
        score += 0.5
    elif structure.last_low is StructurePoint.LL:
        score -= 0.5
    return score


def detect_trend(
    closes: Sequence[float],
    structure: StructureState,
) -> TrendState:
    """Aggregate EMA stack, EMA20 slope and structure into a trend verdict."""
    if not closes:
        return TrendState(direction=TrendDirection.SIDEWAYS, strength=TrendStrength.NONE, score=0.0)

    ema20_series = ema(closes, 20)
    ema20 = ema20_series[-1] if ema20_series else None
    ema50_series = ema(closes, 50)
    ema50 = ema50_series[-1] if ema50_series else None
    price = closes[-1]

    stack = _ema_stack_score(price, ema20, ema50)
    slope = _slope_score(ema20_series)
    struct = _structure_score(structure)

    # Weighted blend; weights sum to 1.0.
    score = 0.4 * stack + 0.3 * slope + 0.3 * struct
    score = max(-1.0, min(1.0, score))

    magnitude = abs(score)
    if magnitude >= _STRONG:
        strength = TrendStrength.STRONG
    elif magnitude >= _WEAK:
        strength = TrendStrength.WEAK
    else:
        strength = TrendStrength.NONE

    if strength is TrendStrength.NONE:
        direction = TrendDirection.SIDEWAYS
    elif score > 0:
        direction = TrendDirection.UP
    else:
        direction = TrendDirection.DOWN

    return TrendState(direction=direction, strength=strength, score=score)
