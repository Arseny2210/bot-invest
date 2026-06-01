"""Output contract of the analysis engine: :class:`AnalysisResult` and parts.

Immutable Pydantic models. Indicator values use ``Decimal`` to stay consistent
with the MOEX DTOs and to avoid binary-float drift in persisted/serialised
output. Probabilities are plain ``float`` in ``[0, 1]`` and always sum to 1.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from moex_analyst.domain.analysis.enums import (
    LevelKind,
    StructurePoint,
    TrendDirection,
    TrendStrength,
    VolumeCondition,
)
from moex_analyst.domain.market.timeframe import Timeframe

__all__ = [
    "AnalysisResult",
    "IndicatorSnapshot",
    "PriceLevel",
    "ProbabilityDistribution",
    "StructureState",
    "SwingPoint",
    "TrendState",
]

_PROB_TOLERANCE = 1e-6


class _FrozenModel(BaseModel):
    """Base for immutable analysis DTOs."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class TrendState(_FrozenModel):
    """Detected trend direction with a strength band and a normalised score."""

    direction: TrendDirection
    strength: TrendStrength
    # Signed slope-derived score in [-1, 1]: positive = up, negative = down.
    score: float = Field(ge=-1.0, le=1.0)


class SwingPoint(_FrozenModel):
    """A confirmed swing high/low and its structure label."""

    index: int = Field(ge=0)
    at: datetime
    price: Decimal
    is_high: bool
    label: StructurePoint


class StructureState(_FrozenModel):
    """Market-structure summary: the sequence of recent HH/HL/LH/LL labels."""

    swings: tuple[SwingPoint, ...]
    last_high: StructurePoint | None = None
    last_low: StructurePoint | None = None

    @property
    def labels(self) -> tuple[StructurePoint, ...]:
        return tuple(s.label for s in self.swings)


class PriceLevel(_FrozenModel):
    """A clustered support or resistance zone."""

    kind: LevelKind
    price: Decimal
    touches: int = Field(ge=1)
    # Relative strength in [0, 1] derived from touch count and recency.
    strength: float = Field(ge=0.0, le=1.0)


class IndicatorSnapshot(_FrozenModel):
    """Latest values of the deterministic indicators.

    Any field may be ``None`` when the series is too short for that indicator's
    warm-up (e.g. EMA50 on a 30-candle series).
    """

    rsi14: Decimal | None = None
    atr14: Decimal | None = None
    ema20: Decimal | None = None
    ema50: Decimal | None = None


class ProbabilityDistribution(_FrozenModel):
    """Mutually-exclusive outcome probabilities; sum to 1.0."""

    bullish: float = Field(ge=0.0, le=1.0)
    bearish: float = Field(ge=0.0, le=1.0)
    sideways: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _check_sum(self) -> ProbabilityDistribution:
        total = self.bullish + self.bearish + self.sideways
        if abs(total - 1.0) > _PROB_TOLERANCE:
            raise ValueError(f"probabilities must sum to 1.0, got {total}")
        return self


class AnalysisResult(_FrozenModel):
    """Complete deterministic analysis for one instrument + timeframe."""

    ticker: str
    timeframe: Timeframe
    as_of: datetime
    candles_analysed: int = Field(ge=0)

    trend: TrendState
    structure: StructureState
    support_levels: tuple[PriceLevel, ...]
    resistance_levels: tuple[PriceLevel, ...]
    volume_condition: VolumeCondition
    indicators: IndicatorSnapshot
    probabilities: ProbabilityDistribution
