"""Analysis timeframe — a pure domain concept.

The set of timeframes the platform reasons about. That H4 is *derived* by
aggregating four H1 bars is a fact about the timeframe itself (domain), whereas
*how* a finer interval is fetched from a particular data source (ISS interval
codes) is an infrastructure concern and lives there.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = ["Timeframe"]


class Timeframe(StrEnum):
    """Supported analysis timeframes."""

    H1 = "1H"
    H4 = "4H"
    D1 = "1D"

    @property
    def is_aggregated(self) -> bool:
        """Whether this timeframe is built by aggregating a finer interval."""
        return self is Timeframe.H4

    @property
    def aggregation_factor(self) -> int:
        """Number of native H1 bars folded into one bar of this timeframe."""
        return 4 if self is Timeframe.H4 else 1
