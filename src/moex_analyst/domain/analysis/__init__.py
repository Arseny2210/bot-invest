"""Deterministic market-analysis engine.

Pure-Python, no I/O, no AI. Consumes the MOEX integration layer's
``CandleSeriesDTO`` and produces an :class:`AnalysisResult` covering trend,
HH/HL/LH/LL structure, support/resistance, volume condition, RSI/ATR/EMA
indicators, and bullish/bearish/sideways probabilities.
"""

from __future__ import annotations

from moex_analyst.domain.analysis.engine import MIN_CANDLES, AnalysisEngine
from moex_analyst.domain.analysis.enums import (
    LevelKind,
    StructurePoint,
    TrendDirection,
    TrendStrength,
    VolumeCondition,
)
from moex_analyst.domain.analysis.errors import AnalysisError, InsufficientDataError
from moex_analyst.domain.analysis.result import (
    AnalysisResult,
    IndicatorSnapshot,
    PriceLevel,
    ProbabilityDistribution,
    StructureState,
    SwingPoint,
    TrendState,
)

__all__ = [
    "MIN_CANDLES",
    "AnalysisEngine",
    "AnalysisError",
    "AnalysisResult",
    "IndicatorSnapshot",
    "InsufficientDataError",
    "LevelKind",
    "PriceLevel",
    "ProbabilityDistribution",
    "StructurePoint",
    "StructureState",
    "SwingPoint",
    "TrendDirection",
    "TrendState",
    "TrendStrength",
    "VolumeCondition",
]
