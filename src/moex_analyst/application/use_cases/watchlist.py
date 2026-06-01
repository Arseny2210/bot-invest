"""Use case: the platform's instrument watchlist.

The MVP tracks a fixed registry of instruments (no per-user lists yet — those
arrive with the persistence stage). This use case exposes that registry as an
application DTO so the presentation layer never imports infrastructure config.
"""

from __future__ import annotations

from moex_analyst.application.use_cases.dto import WatchedInstrument, Watchlist
from moex_analyst.infrastructure.moex import INSTRUMENT_REGISTRY

__all__ = ["WatchlistUseCase"]


class WatchlistUseCase:
    """Returns the set of instruments the platform tracks."""

    async def execute(self) -> Watchlist:
        """List tracked instruments in registry order."""
        instruments = tuple(
            WatchedInstrument(
                ticker=ref.ticker,
                secid=ref.secid,
                market_type=ref.market_type,
            )
            for ref in INSTRUMENT_REGISTRY.values()
        )
        return Watchlist(instruments=instruments)
