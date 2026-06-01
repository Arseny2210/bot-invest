"""Support / resistance detection by clustering confirmed swing points.

Swing lows are clustered into support zones and swing highs into resistance
zones. Two swings join the same cluster when their prices are within
``tolerance`` (a fraction of price, ATR-free so the module stays independent of
the indicator layer). Each zone's strength grows with touch count and recency.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from moex_analyst.domain.analysis.enums import LevelKind
from moex_analyst.domain.analysis.result import PriceLevel, SwingPoint

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["DEFAULT_CLUSTER_TOLERANCE", "detect_levels"]

# Relative price tolerance for merging swings into one zone (0.4%).
DEFAULT_CLUSTER_TOLERANCE = Decimal("0.004")


def _cluster(
    points: list[tuple[int, Decimal]],
    tolerance: Decimal,
    last_index: int,
    kind: LevelKind,
) -> list[PriceLevel]:
    """Cluster (index, price) swing points of one kind into price levels."""
    if not points:
        return []

    ordered = sorted(points, key=lambda p: p[1])
    clusters: list[list[tuple[int, Decimal]]] = [[ordered[0]]]
    for idx, price in ordered[1:]:
        anchor = clusters[-1][0][1]
        if anchor != 0 and abs(price - anchor) / abs(anchor) <= tolerance:
            clusters[-1].append((idx, price))
        else:
            clusters.append([(idx, price)])

    span = max(last_index, 1)
    levels: list[PriceLevel] = []
    for group in clusters:
        touches = len(group)
        prices = [p for _, p in group]
        mean_price = sum(prices) / Decimal(touches)
        newest = max(idx for idx, _ in group)
        recency = newest / span  # 0..1, newer = stronger
        touch_factor = 1.0 - 1.0 / (1.0 + touches)  # 1->0.5, 2->0.66, 3->0.75
        strength = max(0.0, min(1.0, 0.5 * touch_factor + 0.5 * recency))
        levels.append(
            PriceLevel(
                kind=kind,
                price=mean_price,
                touches=touches,
                strength=strength,
            ),
        )
    return levels


def detect_levels(
    swings: Sequence[SwingPoint],
    *,
    last_index: int,
    tolerance: Decimal = DEFAULT_CLUSTER_TOLERANCE,
) -> tuple[tuple[PriceLevel, ...], tuple[PriceLevel, ...]]:
    """Return ``(support_levels, resistance_levels)`` sorted strongest-first.

    Args:
        swings: confirmed swing points from structure detection.
        last_index: index of the most recent candle (for recency weighting).
        tolerance: relative price distance for merging swings into a zone.
    """
    lows = [(s.index, s.price) for s in swings if not s.is_high]
    highs = [(s.index, s.price) for s in swings if s.is_high]

    supports = _cluster(lows, tolerance, last_index, LevelKind.SUPPORT)
    resistances = _cluster(highs, tolerance, last_index, LevelKind.RESISTANCE)

    supports.sort(key=lambda lvl: lvl.strength, reverse=True)
    resistances.sort(key=lambda lvl: lvl.strength, reverse=True)
    return tuple(supports), tuple(resistances)
