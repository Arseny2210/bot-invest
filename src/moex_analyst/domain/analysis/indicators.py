"""Deterministic technical indicators.

Pure functions over ordered price sequences. No state, no I/O, no randomness —
identical input always yields identical output. Calculations operate on
``float`` internally for speed and are converted to ``Decimal`` by the engine
when assembling the result.

Conventions (fixed and tested):
    * EMA is SMA-seeded: the first EMA value is the SMA of the first ``period``
      samples; subsequent values use the multiplier ``2 / (period + 1)``. This
      makes the result independent of how much extra history precedes the
      warm-up window.
    * RSI and ATR use Wilder's smoothing (RMA), seeded with a simple average of
      the first ``period`` deltas / true ranges. ``RMA`` is shared so RSI and
      ATR cannot diverge in their smoothing.
"""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = [
    "atr",
    "ema",
    "ema_last",
    "rma",
    "rsi",
    "rsi_last",
    "sma",
    "true_ranges",
]


def sma(values: Sequence[float], period: int) -> float | None:
    """Simple moving average of the last ``period`` values.

    Returns ``None`` when there are fewer than ``period`` values.
    """
    if period <= 0:
        raise ValueError("period must be positive")
    if len(values) < period:
        return None
    window = values[-period:]
    return sum(window) / period


def ema(values: Sequence[float], period: int) -> list[float]:
    """Full EMA series (SMA-seeded), one value per input from index ``period-1``.

    The returned list has length ``len(values) - period + 1`` and is empty when
    the input is shorter than ``period``.
    """
    if period <= 0:
        raise ValueError("period must be positive")
    n = len(values)
    if n < period:
        return []
    multiplier = 2.0 / (period + 1)
    seed = sum(values[:period]) / period
    out = [seed]
    prev = seed
    for value in values[period:]:
        prev = (value - prev) * multiplier + prev
        out.append(prev)
    return out


def ema_last(values: Sequence[float], period: int) -> float | None:
    """Final EMA value, or ``None`` if the series is too short."""
    series = ema(values, period)
    return series[-1] if series else None


def rma(values: Sequence[float], period: int) -> list[float]:
    """Wilder's smoothed moving average (RMA), simple-average seeded.

    Used by both RSI and ATR. Returns a series of length
    ``len(values) - period + 1`` (empty if too short).
    """
    if period <= 0:
        raise ValueError("period must be positive")
    n = len(values)
    if n < period:
        return []
    seed = sum(values[:period]) / period
    out = [seed]
    prev = seed
    for value in values[period:]:
        prev = (prev * (period - 1) + value) / period
        out.append(prev)
    return out


def rsi(closes: Sequence[float], period: int = 14) -> list[float]:
    """Relative Strength Index (Wilder). Values are in ``[0, 100]``.

    Returns a series aligned to the deltas (length
    ``len(closes) - period``), empty if the input is too short.
    """
    if period <= 0:
        raise ValueError("period must be positive")
    if len(closes) < period + 1:
        return []

    gains: list[float] = []
    losses: list[float] = []
    for prev, curr in itertools.pairwise(closes):
        delta = curr - prev
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))

    avg_gain = rma(gains, period)
    avg_loss = rma(losses, period)

    out: list[float] = []
    for g, loss in zip(avg_gain, avg_loss, strict=True):
        if loss == 0.0:
            out.append(100.0 if g > 0.0 else 50.0)
        else:
            rs = g / loss
            out.append(100.0 - (100.0 / (1.0 + rs)))
    return out


def rsi_last(closes: Sequence[float], period: int = 14) -> float | None:
    """Final RSI value, or ``None`` if the series is too short."""
    series = rsi(closes, period)
    return series[-1] if series else None


def true_ranges(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
) -> list[float]:
    """Per-bar True Range. The first bar uses ``high - low`` (no prior close)."""
    if not (len(highs) == len(lows) == len(closes)):
        raise ValueError("highs, lows, closes must be the same length")
    if not highs:
        return []
    out = [highs[0] - lows[0]]
    for i in range(1, len(highs)):
        prev_close = closes[i - 1]
        out.append(
            max(
                highs[i] - lows[i],
                abs(highs[i] - prev_close),
                abs(lows[i] - prev_close),
            ),
        )
    return out


def atr(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    period: int = 14,
) -> float | None:
    """Average True Range (Wilder). Returns ``None`` if the series is too short."""
    tr = true_ranges(highs, lows, closes)
    smoothed = rma(tr, period)
    return smoothed[-1] if smoothed else None
