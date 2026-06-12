"""Analysis timeframe — a pure domain concept.

The set of timeframes the platform reasons about. Some timeframes are *derived*
by aggregating finer candles (H4 folds 4x 1H, W1 folds 5x 1D), whereas
*how* a particular interval is fetched from a given data source is an
infrastructure concern and lives there.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = ["Timeframe"]


class Timeframe(StrEnum):
    """Supported analysis timeframes."""

    M15 = "15M"
    H1 = "1H"
    H4 = "4H"
    D1 = "1D"
    W1 = "1W"

    @property
    def is_aggregated(self) -> bool:
        """Whether this timeframe is built by aggregating a finer interval."""
        return self in (Timeframe.H4, Timeframe.W1)

    @property
    def aggregation_factor(self) -> int:
        """Number of native bars folded into one bar of this timeframe."""
        if self is Timeframe.H4:
            return 4
        if self is Timeframe.W1:
            return 5
        return 1
