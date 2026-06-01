"""Candle service: fetch 1H / 1D candles and derive 4H by aggregation.

MOEX ISS exposes 1H (interval=60) and 1D (interval=24) candles but no native
4H. The 4H timeframe is built here by folding consecutive 1H candles into
4-bar buckets aligned to the hour-of-day. Candle history is fetched with the
ISS ``start`` cursor to page through results beyond the per-response limit.
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
    from collections.abc import Sequence
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

        For :attr:`Timeframe.H4` the data is fetched at 1H and aggregated.
        ``date_from``/``date_till`` are inclusive ISS calendar bounds (Moscow
        dates); omitting them lets ISS apply its own default window.
        """
        ref = resolve_instrument(ticker)
        raw = await self._fetch_native(ref, timeframe, date_from, date_till)

        candles = tuple(_aggregate_4h(raw)) if timeframe.is_aggregated else tuple(raw)
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


def _aggregate_4h(candles: Sequence[CandleDTO]) -> list[CandleDTO]:
    """Fold 1H candles into 4H bars aligned to 00:00/04:00/08:00... UTC-hour.

    Bars are grouped by ``(date, hour // 4)`` of each candle's ``begin``. Within
    a bucket: open = first open, close = last close, high = max high, low = min
    low, volume/value = sums. Buckets are emitted in chronological order. A
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

    result: list[CandleDTO] = []
    for key in order:
        group = buckets[key]
        result.append(
            CandleDTO(
                begin=group[0].begin,
                end=group[-1].end,
                open=group[0].open,
                high=max(c.high for c in group),
                low=min(c.low for c in group),
                close=group[-1].close,
                volume=sum(c.volume for c in group),
                value=sum((c.value for c in group), Decimal(0)),
            )
        )
    return result
