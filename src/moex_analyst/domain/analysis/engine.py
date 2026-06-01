"""Analysis engine orchestrator.

Consumes a domain :class:`CandleSeries` and produces a single
:class:`AnalysisResult`. The engine depends only on the domain: infrastructure
DTOs are mapped to :class:`CandleSeries` upstream (see
``infrastructure/moex/mapping.py``). The engine itself does no I/O: it extracts
price/volume series, delegates to the deterministic submodules, and assembles
the immutable result.

The same engine serves 1H / 4H / 1D — the timeframe is carried through from the
input series (4H aggregation happens upstream in the candle service, so by the
time a series reaches here every candle is already one bar of its timeframe).
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from moex_analyst.domain.analysis.errors import InsufficientDataError
from moex_analyst.domain.analysis.indicators import atr, ema_last, rsi_last
from moex_analyst.domain.analysis.levels import detect_levels
from moex_analyst.domain.analysis.probability import estimate_probabilities
from moex_analyst.domain.analysis.result import (
    AnalysisResult,
    IndicatorSnapshot,
)
from moex_analyst.domain.analysis.structure import DEFAULT_SWING_WINDOW, detect_structure
from moex_analyst.domain.analysis.trend import detect_trend
from moex_analyst.domain.analysis.volume import classify_volume

if TYPE_CHECKING:
    from moex_analyst.domain.market.candle import CandleSeries

__all__ = ["MIN_CANDLES", "AnalysisEngine"]

# Minimum bars to attempt analysis at all. Below this nothing meaningful can be
# computed (RSI14 needs 15, swing window needs 2*k+1). Indicators that need more
# history (EMA50) degrade to ``None`` individually rather than failing the run.
MIN_CANDLES = 15


def _quantize(value: float | None, places: int) -> Decimal | None:
    if value is None:
        return None
    quant = Decimal(1).scaleb(-places)
    return Decimal(str(value)).quantize(quant)


class AnalysisEngine:
    """Deterministic market-analysis engine.

    Stateless and reusable across instruments and timeframes. Construct once and
    call :meth:`analyse` per series.
    """

    def __init__(
        self,
        *,
        swing_window: int = DEFAULT_SWING_WINDOW,
        price_decimals: int = 4,
    ) -> None:
        self._swing_window = swing_window
        self._price_decimals = price_decimals

    def analyse(self, series: CandleSeries) -> AnalysisResult:
        """Analyse a candle series into a complete :class:`AnalysisResult`.

        Raises:
            InsufficientDataError: if the series has fewer than :data:`MIN_CANDLES`.
        """
        candles = series.candles
        count = len(candles)
        if count < MIN_CANDLES:
            raise InsufficientDataError(
                required=MIN_CANDLES,
                got=count,
                detail=f"{series.ticker}/{series.timeframe.value}",
            )

        highs_d = [c.high for c in candles]
        lows_d = [c.low for c in candles]
        closes_d = [c.close for c in candles]
        times = [c.begin for c in candles]
        volumes = [c.volume for c in candles]

        highs = [float(h) for h in highs_d]
        lows = [float(low) for low in lows_d]
        closes = [float(c) for c in closes_d]

        # --- indicators -----------------------------------------------------
        rsi14 = rsi_last(closes, 14)
        atr14 = atr(highs, lows, closes, 14)
        ema20 = ema_last(closes, 20)
        ema50 = ema_last(closes, 50)
        indicators = IndicatorSnapshot(
            rsi14=_quantize(rsi14, 2),
            atr14=_quantize(atr14, self._price_decimals),
            ema20=_quantize(ema20, self._price_decimals),
            ema50=_quantize(ema50, self._price_decimals),
        )

        # --- structure / levels --------------------------------------------
        structure = detect_structure(
            highs_d, lows_d, times, window=self._swing_window,
        )
        supports, resistances = detect_levels(
            structure.swings, last_index=count - 1,
        )

        # --- trend / volume / probabilities --------------------------------
        trend = detect_trend(closes, structure)
        volume_condition = classify_volume(volumes)
        probabilities = estimate_probabilities(
            trend, structure, rsi14, volume_condition,
        )

        return AnalysisResult(
            ticker=series.ticker,
            timeframe=series.timeframe,
            as_of=times[-1],
            candles_analysed=count,
            trend=trend,
            structure=structure,
            support_levels=supports,
            resistance_levels=resistances,
            volume_condition=volume_condition,
            indicators=indicators,
            probabilities=probabilities,
        )
