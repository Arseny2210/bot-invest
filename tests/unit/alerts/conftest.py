"""Builders for alert unit tests.

These construct :class:`AnalysisResult` snapshots directly (bypassing the
analysis engine) so each alert rule can be exercised against a precisely
controlled input.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from moex_analyst.domain.analysis.enums import (
    LevelKind,
    StructurePoint,
    TrendDirection,
    TrendStrength,
    VolumeCondition,
)
from moex_analyst.domain.analysis.result import (
    AnalysisResult,
    IndicatorSnapshot,
    PriceLevel,
    ProbabilityDistribution,
    StructureState,
    SwingPoint,
    TrendState,
)
from moex_analyst.domain.market.timeframe import Timeframe

_AS_OF = datetime(2024, 6, 1, 12, tzinfo=UTC)


def make_level(
    kind: LevelKind,
    price: float,
    *,
    touches: int = 2,
    strength: float = 0.5,
) -> PriceLevel:
    return PriceLevel(
        kind=kind,
        price=Decimal(str(price)),
        touches=touches,
        strength=strength,
    )


def make_swing(
    index: int,
    price: float,
    *,
    is_high: bool,
    label: StructurePoint,
) -> SwingPoint:
    return SwingPoint(
        index=index,
        at=_AS_OF,
        price=Decimal(str(price)),
        is_high=is_high,
        label=label,
    )


def make_result(
    *,
    ticker: str = "TEST",
    timeframe: Timeframe = Timeframe.H1,
    candles_analysed: int = 60,
    trend: TrendState | None = None,
    structure: StructureState | None = None,
    support_levels: tuple[PriceLevel, ...] = (),
    resistance_levels: tuple[PriceLevel, ...] = (),
    volume_condition: VolumeCondition = VolumeCondition.NORMAL,
    indicators: IndicatorSnapshot | None = None,
    probabilities: ProbabilityDistribution | None = None,
) -> AnalysisResult:
    """Build an :class:`AnalysisResult` with neutral defaults and targeted overrides.

    Defaults are deliberately *quiet*: no levels, sideways trend, empty
    structure, normal volume and a near-uniform probability split — so a result
    with only the defaults raises no alerts and each test can switch on exactly
    the rule it targets.
    """
    return AnalysisResult(
        ticker=ticker,
        timeframe=timeframe,
        as_of=_AS_OF,
        candles_analysed=candles_analysed,
        trend=trend
        or TrendState(
            direction=TrendDirection.SIDEWAYS,
            strength=TrendStrength.NONE,
            score=0.0,
        ),
        structure=structure or StructureState(swings=()),
        support_levels=support_levels,
        resistance_levels=resistance_levels,
        volume_condition=volume_condition,
        indicators=indicators or IndicatorSnapshot(),
        probabilities=probabilities
        or ProbabilityDistribution(bullish=0.34, bearish=0.33, sideways=0.33),
    )
