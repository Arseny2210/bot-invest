"""Analysis-layer exceptions.

These are domain errors raised by the deterministic engine. They are distinct
from infrastructure errors (MOEX/DB) so use cases can reason about "the data
was insufficient to analyse" separately from "the data source failed".
"""

from __future__ import annotations

__all__ = ["AnalysisError", "InsufficientDataError"]


class AnalysisError(Exception):
    """Base class for all analysis-engine errors."""


class InsufficientDataError(AnalysisError):
    """Raised when a series has too few candles to compute the analysis.

    Carries how many candles were supplied versus the minimum required, so the
    caller can surface an actionable message.
    """

    def __init__(self, *, required: int, got: int, detail: str = "") -> None:
        self.required = required
        self.got = got
        suffix = f" ({detail})" if detail else ""
        super().__init__(
            f"insufficient candles: need at least {required}, got {got}{suffix}",
        )
