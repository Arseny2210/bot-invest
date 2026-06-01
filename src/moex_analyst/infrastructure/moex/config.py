"""MOEX ISS endpoint configuration and the target-instrument registry.

This module holds the static facts about *what* we fetch and *from where*:
the ISS base path conventions, the timeframe→interval mapping, and the fixed
registry of the six instruments the platform tracks. It contains no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

# Timeframe is a domain concept; infrastructure depends inward on it and is
# re-exported here for the convenience of the MOEX layer's public surface.
from moex_analyst.domain.market.timeframe import Timeframe

__all__ = [
    "INSTRUMENT_REGISTRY",
    "InstrumentRef",
    "MarketType",
    "Timeframe",
    "iss_interval",
    "resolve_instrument",
]


class MarketType(StrEnum):
    """ISS market classification relevant to this platform."""

    INDEX = "index"
    SHARES = "shares"


# ISS numeric `interval` query values. 60 = 1 hour, 24 = 1 day.
# MOEX ISS has no native 4H interval, so H4 is fetched at 1H (interval 60) and
# aggregated client-side in the candle service.
_ISS_INTERVAL: dict[Timeframe, int] = {
    Timeframe.H1: 60,
    Timeframe.H4: 60,
    Timeframe.D1: 24,
}


def iss_interval(timeframe: Timeframe) -> int:
    """Return the ISS ``interval`` query value used to fetch ``timeframe``."""
    return _ISS_INTERVAL[timeframe]


@dataclass(frozen=True, slots=True)
class InstrumentRef:
    """Static routing facts for one tracked instrument.

    ``ticker`` is the platform-facing symbol; ``secid`` is the ISS security id
    (they differ for YAKOVLEV, whose ISS secid is ``IRKT``). ``engine`` /
    ``market`` / ``board`` locate the security within the ISS URL hierarchy.
    """

    ticker: str
    secid: str
    market_type: MarketType
    engine: str
    market: str
    board: str

    @property
    def candles_path(self) -> str:
        """ISS path (relative to base) for this instrument's candles."""
        return (
            f"engines/{self.engine}/markets/{self.market}"
            f"/boards/{self.board}/securities/{self.secid}/candles.json"
        )

    @property
    def marketdata_path(self) -> str:
        """ISS path (relative to base) for this instrument's live marketdata."""
        return (
            f"engines/{self.engine}/markets/{self.market}"
            f"/boards/{self.board}/securities/{self.secid}.json"
        )

    @property
    def description_path(self) -> str:
        """ISS path (relative to base) for this instrument's static metadata."""
        return f"securities/{self.secid}.json"


# The fixed set of tracked instruments. Boards/markets verified against the live
# ISS API. IMOEX is an index (engine=stock, market=index, board=SNDX); the rest
# are ordinary shares on TQBR. YAKOVLEV trades under ISS secid IRKT.
INSTRUMENT_REGISTRY: dict[str, InstrumentRef] = {
    "IMOEX": InstrumentRef("IMOEX", "IMOEX", MarketType.INDEX, "stock", "index", "SNDX"),
    "UWGN": InstrumentRef("UWGN", "UWGN", MarketType.SHARES, "stock", "shares", "TQBR"),
    "SNGS": InstrumentRef("SNGS", "SNGS", MarketType.SHARES, "stock", "shares", "TQBR"),
    "SGZH": InstrumentRef("SGZH", "SGZH", MarketType.SHARES, "stock", "shares", "TQBR"),
    "VTBR": InstrumentRef("VTBR", "VTBR", MarketType.SHARES, "stock", "shares", "TQBR"),
    "YAKOVLEV": InstrumentRef("YAKOVLEV", "IRKT", MarketType.SHARES, "stock", "shares", "TQBR"),
}


def resolve_instrument(ticker: str) -> InstrumentRef:
    """Look up an :class:`InstrumentRef` by platform ticker (case-insensitive).

    Raises:
        KeyError: if ``ticker`` is not one of the tracked instruments.
    """
    return INSTRUMENT_REGISTRY[ticker.strip().upper()]
