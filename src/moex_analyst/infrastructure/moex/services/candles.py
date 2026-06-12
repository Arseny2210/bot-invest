"""Candle service: fetch native candles and derive aggregated timeframes.

MOEX ISS exposes 1H (interval=60), 1D (interval=24) and 15M (interval=15)
candles natively. H4 is built by folding 1H bars into 4-bar buckets; W1 is
built by folding 1D bars into 5-bar weekly buckets. Candle history is fetched
with the ISS ``start`` cursor to page through results beyond the per-response
limit.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from moex_analyst.infrastructure.moex.config import (
    Timeframe,
    iss_interval,
    resolve_instrument,
)
from moex_analyst.infrastructure.moex.dto import CandleDTO, CandleSeriesDTO
from moex_analyst.infrastructure.moex.parsing.mapper import map_candle
from moex_analyst.infrastructure.moex.parsing.parser import parse_block

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from datetime import date

    from moex_analyst.infrastructure.moex.config import InstrumentRef
    from moex_analyst.infrastructure.moex.transport.client import MoexHttpClient

__all__ = ["CandleService"]

# ISS caps candle rows per response; page until a short page is returned.
_PAGE_LIMIT = 500
_MAX_PAGES = 100  # hard stop guarding against pathological pagination loops


class CandleService:
    """Fetches OHLCV candles for tracked instruments across timeframes."""

    def __init__(self, client: MoexHttpClient) -> None:
        self._client = client

    async def get_candles(
        self,
        ticker: str,
        timeframe: Timeframe,
        *,
        date_from: date | None = None,
        date_till: date | None = None,
    ) -> CandleSeriesDTO:
        """Fetch candles for ``ticker`` at ``timeframe``.

        For aggregated timeframes (:attr:`Timeframe.H4`, :attr:`Timeframe.W1`)
        the data is fetched at the underlying native interval and folded into
        bars. ``date_from``/``date_till`` are inclusive ISS calendar bounds
        (Moscow dates); omitting them lets ISS apply its own default window.
        """
        ref = resolve_instrument(ticker)
        raw = await self._fetch_native(ref, timeframe, date_from, date_till)

        aggregator = _AGGREGATORS.get(timeframe)
        candles = tuple(aggregator(raw)) if aggregator else tuple(raw)
        return CandleSeriesDTO(ticker=ref.ticker, timeframe=timeframe, candles=candles)

    async def _fetch_native(
        self,
        ref: InstrumentRef,
        timeframe: Timeframe,
        date_from: date | None,
        date_till: date | None,
    ) -> list[CandleDTO]:
        """Page through ISS candles at the native interval for ``timeframe``."""
        base_params: dict[str, Any] = {"interval": iss_interval(timeframe)}
        if date_from is not None:
            base_params["from"] = date_from.isoformat()
        if date_till is not None:
            base_params["till"] = date_till.isoformat()

        collected: list[CandleDTO] = []
        start = 0
        for _ in range(_MAX_PAGES):
            payload = await self._client.get_json(
                ref.candles_path,
                params={**base_params, "start": start},
            )
            records = parse_block(payload, "candles")
            if not records:
                break
            collected.extend(map_candle(r) for r in records)
            if len(records) < _PAGE_LIMIT:
                break
            start += len(records)
        return collected


def _make_ohlcv(group: Sequence[CandleDTO]) -> CandleDTO:
    """Merge a candle sequence into one OHLCV bar (open=first, close=last)."""
    return CandleDTO(
        begin=group[0].begin,
        end=group[-1].end,
        open=group[0].open,
        high=max(c.high for c in group),
        low=min(c.low for c in group),
        close=group[-1].close,
        volume=sum(c.volume for c in group),
        value=sum((c.value for c in group), Decimal(0)),
    )


def _aggregate_4h(candles: Sequence[CandleDTO]) -> list[CandleDTO]:
    """Fold 1H candles into 4H bars aligned to 00:00/04:00/08:00... UTC-hour.

    Bars are grouped by ``(date, hour // 4)`` of each candle's ``begin``. A
    partial trailing bucket (fewer than 4 hours) is still emitted so the latest,
    in-progress 4H bar is available to callers.
    """
    buckets: dict[tuple[date, int], list[CandleDTO]] = {}
    order: list[tuple[date, int]] = []
    for candle in candles:
        key = (candle.begin.date(), candle.begin.hour // 4)
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(candle)
    return [_make_ohlcv(buckets[k]) for k in order]


def _aggregate_weekly(candles: Sequence[CandleDTO]) -> list[CandleDTO]:
    """Fold D1 candles into weekly bars by ISO week number.

    Groups by ``(iso_year, iso_week)``. A partial week (e.g. current
    in-progress week) is still emitted.
    """
    buckets: dict[tuple[int, int], list[CandleDTO]] = {}
    order: list[tuple[int, int]] = []
    for candle in candles:
        iso = candle.begin.isocalendar()
        key = (iso[0], iso[1])
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(candle)
    return [_make_ohlcv(buckets[k]) for k in order]


_AGGREGATORS: dict[Timeframe, Callable[[Sequence[CandleDTO]], list[CandleDTO]]] = {
    Timeframe.H4: _aggregate_4h,
    Timeframe.W1: _aggregate_weekly,
}
