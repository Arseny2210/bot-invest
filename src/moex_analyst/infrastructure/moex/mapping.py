"""Anti-corruption mapping: MOEX transport DTOs -> domain value objects.

This is the seam between the integration layer and the domain. The analysis
engine consumes only domain :class:`Candle` / :class:`CandleSeries`; nothing in
the domain imports a MOEX DTO. Mapping lives here in infrastructure, which is
allowed to depend inward on the domain.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from moex_analyst.domain.market.candle import Candle, CandleSeries

if TYPE_CHECKING:
    from moex_analyst.infrastructure.moex.dto import CandleDTO, CandleSeriesDTO

__all__ = ["candle_series_to_domain", "candle_to_domain"]


def candle_to_domain(dto: CandleDTO) -> Candle:
    """Map one transport :class:`CandleDTO` to a domain :class:`Candle`."""
    return Candle(
        begin=dto.begin,
        end=dto.end,
        open=dto.open,
        high=dto.high,
        low=dto.low,
        close=dto.close,
        volume=dto.volume,
        value=dto.value,
    )


def candle_series_to_domain(dto: CandleSeriesDTO) -> CandleSeries:
    """Map a transport :class:`CandleSeriesDTO` to a domain :class:`CandleSeries`.

    ``timeframe`` is already the domain :class:`~moex_analyst.domain.market.timeframe.Timeframe`
    (the DTO references the domain enum), so it carries over directly.
    """
    return CandleSeries(
        ticker=dto.ticker,
        timeframe=dto.timeframe,
        candles=tuple(candle_to_domain(c) for c in dto.candles),
    )
