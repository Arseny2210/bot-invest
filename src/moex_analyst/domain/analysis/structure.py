"""Market-structure detection: swing points and HH/HL/LH/LL labelling.

A swing high is a bar whose high is strictly greater than the highs of ``k``
bars on each side (mirror for swing low). Requiring ``k`` confirming bars to the
right means swings are confirmed with a lag and never repaint. Each confirmed
swing is labelled relative to the previous swing of the same kind (high vs low).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from moex_analyst.domain.analysis.enums import StructurePoint
from moex_analyst.domain.analysis.result import StructureState, SwingPoint

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime
    from decimal import Decimal

__all__ = ["DEFAULT_SWING_WINDOW", "detect_structure"]

DEFAULT_SWING_WINDOW = 2


def _is_swing_high(highs: Sequence[float], i: int, k: int) -> bool:
    pivot = highs[i]
    for j in range(i - k, i + k + 1):
        if j == i:
            continue
        if highs[j] >= pivot:
            return False
    return True


def _is_swing_low(lows: Sequence[float], i: int, k: int) -> bool:
    pivot = lows[i]
    for j in range(i - k, i + k + 1):
        if j == i:
            continue
        if lows[j] <= pivot:
            return False
    return True


def detect_structure(
    highs: Sequence[Decimal],
    lows: Sequence[Decimal],
    times: Sequence[datetime],
    *,
    window: int = DEFAULT_SWING_WINDOW,
) -> StructureState:
    """Detect confirmed swings and label them HH/HL/LH/LL.

    Args:
        highs/lows: per-bar high/low prices (``Decimal``), index-aligned.
        times: per-bar timestamps, index-aligned.
        window: number of confirming bars on each side of a pivot (``k``).

    Returns an empty :class:`StructureState` when there are too few bars to
    confirm any swing.
    """
    n = len(highs)
    if not (n == len(lows) == len(times)):
        raise ValueError("highs, lows, times must be the same length")
    if window < 1:
        raise ValueError("window must be >= 1")

    # Float views for the comparison-only pivot test; labels use Decimal prices.
    fh = [float(h) for h in highs]
    fl = [float(low) for low in lows]

    swings: list[SwingPoint] = []
    prev_high: Decimal | None = None
    prev_low: Decimal | None = None
    last_high_label: StructurePoint | None = None
    last_low_label: StructurePoint | None = None

    for i in range(window, n - window):
        if _is_swing_high(fh, i, window):
            price = highs[i]
            if prev_high is None:
                label = StructurePoint.HH  # first high: seed as higher-high
            else:
                label = StructurePoint.HH if price > prev_high else StructurePoint.LH
            prev_high = price
            last_high_label = label
            swings.append(
                SwingPoint(index=i, at=times[i], price=price, is_high=True, label=label),
            )
        elif _is_swing_low(fl, i, window):
            price = lows[i]
            if prev_low is None:
                label = StructurePoint.HL  # first low: seed as higher-low
            else:
                label = StructurePoint.HL if price > prev_low else StructurePoint.LL
            prev_low = price
            last_low_label = label
            swings.append(
                SwingPoint(index=i, at=times[i], price=price, is_high=False, label=label),
            )

    return StructureState(
        swings=tuple(swings),
        last_high=last_high_label,
        last_low=last_low_label,
    )
