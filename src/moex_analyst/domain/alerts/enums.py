"""Enumerations for the deterministic alert engine.

Pure value types shared across the alert submodules. No I/O, no framework
dependencies — safe to import from anywhere in the domain layer.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = [
    "AlertDirection",
    "AlertSeverity",
    "AlertType",
]


class AlertType(StrEnum):
    """The kinds of alert the engine can raise from an analysis snapshot."""

    SUPPORT_BREAKDOWN = "support_breakdown"
    RESISTANCE_BREAKOUT = "resistance_breakout"
    TREND_CHANGE = "trend_change"
    EMA20_CROSS_EMA50 = "ema20_cross_ema50"
    RSI_OVERBOUGHT = "rsi_overbought"
    RSI_OVERSOLD = "rsi_oversold"
    VOLUME_SPIKE = "volume_spike"
    MARKET_STRUCTURE_CHANGE = "market_structure_change"
    STRONG_BULLISH_SIGNAL = "strong_bullish_signal"
    STRONG_BEARISH_SIGNAL = "strong_bearish_signal"


class AlertDirection(StrEnum):
    """Directional bias an alert implies for the instrument."""

    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class AlertSeverity(StrEnum):
    """How strongly the caller should weight an alert.

    Ordering (INFO < WARNING < CRITICAL) is encoded by :attr:`rank` rather than
    by enum member order so it stays explicit and stable across refactors.
    """

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

    @property
    def rank(self) -> int:
        """Monotonic numeric rank for sorting/comparison (higher = stronger)."""
        return _SEVERITY_RANK[self]


_SEVERITY_RANK: dict[AlertSeverity, int] = {
    AlertSeverity.INFO: 0,
    AlertSeverity.WARNING: 1,
    AlertSeverity.CRITICAL: 2,
}
