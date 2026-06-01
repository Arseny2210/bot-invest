"""Mappers: ISS records (from the parser) → typed DTOs.

This is the only place that knows ISS column names, the Moscow timezone of ISS
timestamps, and how to coerce raw JSON scalars into ``Decimal`` / ``int``. The
``description`` block is a key/value table (one row per attribute), unlike the
tabular ``candles``/``marketdata`` blocks, so it is handled separately.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from moex_analyst.infrastructure.moex.dto import CandleDTO, InstrumentDTO, QuoteDTO
from moex_analyst.infrastructure.moex.errors import MoexResponseError

if TYPE_CHECKING:
    from moex_analyst.infrastructure.moex.config import InstrumentRef

__all__ = [
    "map_candle",
    "map_description",
    "map_marketdata",
]

# ISS reports timestamps in Moscow local time, without an offset.
_MSK = ZoneInfo("Europe/Moscow")
_ISS_DT_FORMAT = "%Y-%m-%d %H:%M:%S"


def _to_utc(raw: Any) -> datetime:
    """Parse a naive Moscow-time ISS timestamp into an aware UTC datetime."""
    if not isinstance(raw, str):
        raise MoexResponseError(f"Expected datetime string, got {type(raw).__name__}")
    try:
        naive = datetime.strptime(raw, _ISS_DT_FORMAT)  # noqa: DTZ007 (tz applied next)
    except ValueError as exc:
        raise MoexResponseError(f"Unparseable ISS datetime: {raw!r}") from exc
    return naive.replace(tzinfo=_MSK).astimezone(UTC)


def _to_utc_optional(raw: Any) -> datetime | None:
    if raw in (None, "", "0000-00-00 00:00:00"):
        return None
    return _to_utc(raw)


def _to_decimal(raw: Any) -> Decimal:
    """Coerce an ISS numeric scalar to ``Decimal`` (via ``str`` for fidelity)."""
    if raw is None:
        raise MoexResponseError("Expected numeric value, got null")
    try:
        return Decimal(str(raw))
    except (InvalidOperation, ValueError) as exc:
        raise MoexResponseError(f"Non-numeric ISS value: {raw!r}") from exc


def _to_decimal_optional(raw: Any) -> Decimal | None:
    if raw is None or raw == "":
        return None
    return _to_decimal(raw)


def _to_int(raw: Any, *, default: int = 0) -> int:
    if raw is None or raw == "":
        return default
    try:
        # Some volume/turnover counters arrive as floats (e.g. 4416.0).
        return int(Decimal(str(raw)))
    except (InvalidOperation, ValueError) as exc:
        raise MoexResponseError(f"Non-integer ISS value: {raw!r}") from exc


def _to_int_optional(raw: Any) -> int | None:
    if raw is None or raw == "":
        return None
    return _to_int(raw)


def map_candle(record: dict[str, Any]) -> CandleDTO:
    """Map one ``candles`` block record to a :class:`CandleDTO`.

    ISS candle columns are ``open, close, high, low, value, volume, begin, end``
    — note ``close`` precedes ``high``/``low``; we map by name, never position.
    """
    return CandleDTO(
        begin=_to_utc(record["begin"]),
        end=_to_utc(record["end"]),
        open=_to_decimal(record["open"]),
        high=_to_decimal(record["high"]),
        low=_to_decimal(record["low"]),
        close=_to_decimal(record["close"]),
        volume=_to_int(record.get("volume")),
        value=_to_decimal(record.get("value", 0)),
    )


def map_description(records: list[dict[str, Any]], ref: InstrumentRef) -> InstrumentDTO:
    """Map the ``description`` key/value block to an :class:`InstrumentDTO`.

    The description block has one row per attribute with ``name``/``value``
    columns, so it is first folded into a flat ``{NAME: value}`` mapping.
    """
    attrs: dict[str, Any] = {}
    for row in records:
        name = row.get("name")
        if isinstance(name, str):
            attrs[name.upper()] = row.get("value")

    shortname = attrs.get("SHORTNAME") or attrs.get("NAME") or ref.ticker
    return InstrumentDTO(
        ticker=ref.ticker,
        secid=ref.secid,
        shortname=str(shortname),
        market_type=ref.market_type,
        board=ref.board,
        currency=str(attrs.get("CURRENCYID") or attrs.get("FACEUNIT") or "RUB"),
        lot_size=_to_int(attrs.get("LOTSIZE"), default=1),
        decimals=_to_int(attrs.get("DECIMALS"), default=2),
    )


def map_marketdata(record: dict[str, Any], ref: InstrumentRef) -> QuoteDTO:
    """Map one ``marketdata`` block record to a :class:`QuoteDTO`."""
    return QuoteDTO(
        secid=ref.secid,
        board=ref.board,
        last=_to_decimal_optional(record.get("LAST")),
        bid=_to_decimal_optional(record.get("BID")),
        offer=_to_decimal_optional(record.get("OFFER")),
        open=_to_decimal_optional(record.get("OPEN")),
        high=_to_decimal_optional(record.get("HIGH")),
        low=_to_decimal_optional(record.get("LOW")),
        value_today=_to_decimal_optional(record.get("VALTODAY")),
        volume_today=_to_int_optional(record.get("VOLTODAY")),
        num_trades=_to_int_optional(record.get("NUMTRADES")),
        updated_at=_resolve_updated_at(record),
    )


def _resolve_updated_at(record: dict[str, Any]) -> datetime | None:
    """Derive an aware UTC update time from ISS marketdata fields.

    Prefers ``SYSTIME`` (full timestamp); falls back to combining today's
    ISS date implicitly via ``UPDATETIME`` is avoided — ``SYSTIME`` is the
    reliable full datetime when present.
    """
    systime = record.get("SYSTIME")
    if isinstance(systime, str) and systime:
        return _to_utc_optional(systime)
    return None
