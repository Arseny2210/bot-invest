"""Unit tests for the MOEX DTO -> domain mapping (anti-corruption layer)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from moex_analyst.domain.market.candle import Candle, CandleSeries
from moex_analyst.domain.market.timeframe import Timeframe
from moex_analyst.infrastructure.moex.config import (
    INSTRUMENT_REGISTRY,
    resolve_instrument,
)
from moex_analyst.infrastructure.moex.dto import CandleDTO, CandleSeriesDTO
from moex_analyst.infrastructure.moex.mapping import (
    candle_series_to_domain,
    candle_to_domain,
)

_BASE = datetime(2024, 1, 1, tzinfo=UTC)


def _candle_dto(i: int, close: float) -> CandleDTO:
    begin = _BASE + timedelta(hours=i)
    return CandleDTO(
        begin=begin,
        end=begin + timedelta(hours=1),
        open=Decimal(str(close)),
        high=Decimal(str(close + 1)),
        low=Decimal(str(close - 1)),
        close=Decimal(str(close)),
        volume=100 + i,
        value=Decimal(str(close * 100)),
    )


class TestCandleMapping:
    def test_maps_all_fields(self) -> None:
        dto = _candle_dto(0, 100.0)
        domain = candle_to_domain(dto)
        assert isinstance(domain, Candle)
        assert domain.begin == dto.begin
        assert domain.end == dto.end
        assert domain.open == dto.open
        assert domain.high == dto.high
        assert domain.low == dto.low
        assert domain.close == dto.close
        assert domain.volume == dto.volume
        assert domain.value == dto.value

    def test_preserves_decimal_precision(self) -> None:
        begin = _BASE
        dto = CandleDTO(
            begin=begin,
            end=begin + timedelta(hours=1),
            open=Decimal("12.3456"),
            high=Decimal("12.9999"),
            low=Decimal("12.0001"),
            close=Decimal("12.5000"),
            volume=0,
            value=Decimal("0"),
        )
        domain = candle_to_domain(dto)
        assert domain.close == Decimal("12.5000")
        assert domain.volume == 0


class TestSeriesMapping:
    def test_maps_series_with_timeframe_and_ticker(self) -> None:
        dto = CandleSeriesDTO(
            ticker="SNGS",
            timeframe=Timeframe.H4,
            candles=tuple(_candle_dto(i, 100.0 + i) for i in range(5)),
        )
        domain = candle_series_to_domain(dto)
        assert isinstance(domain, CandleSeries)
        assert domain.ticker == "SNGS"
        assert domain.timeframe is Timeframe.H4
        assert len(domain.candles) == 5
        assert all(isinstance(c, Candle) for c in domain.candles)

    def test_order_preserved(self) -> None:
        dto = CandleSeriesDTO(
            ticker="VTBR",
            timeframe=Timeframe.D1,
            candles=tuple(_candle_dto(i, 50.0 + i) for i in range(10)),
        )
        domain = candle_series_to_domain(dto)
        assert [c.close for c in domain.candles] == [c.close for c in dto.candles]

    def test_empty_series(self) -> None:
        dto = CandleSeriesDTO(ticker="UWGN", timeframe=Timeframe.H1, candles=())
        domain = candle_series_to_domain(dto)
        assert domain.is_empty
        assert domain.latest is None


# ---------------------------------------------------------------------------
# IRKT / YAKOVLEV mapping
# ---------------------------------------------------------------------------


class TestIrktResolution:
    def test_irk_resolves_via_direct_key(self) -> None:
        ref = resolve_instrument("IRKT")
        assert ref.ticker == "IRKT"
        assert ref.secid == "IRKT"

    def test_yakovlev_alias_resolves_to_irk(self) -> None:
        ref = resolve_instrument("YAKOVLEV")
        assert ref.ticker == "IRKT"
        assert ref.secid == "IRKT"

    def test_case_insensitive_resolution(self) -> None:
        ref = resolve_instrument("irkt")
        assert ref.ticker == "IRKT"

    def test_irk_in_registry(self) -> None:
        assert "IRKT" in INSTRUMENT_REGISTRY

    def test_no_yakovlev_in_registry(self) -> None:
        assert "YAKOVLEV" not in INSTRUMENT_REGISTRY

    def test_unknown_ticker_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            resolve_instrument("UNKNOWN")
