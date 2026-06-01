"""Current price / marketdata service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from moex_analyst.infrastructure.moex.config import resolve_instrument
from moex_analyst.infrastructure.moex.errors import MoexEmptyDataError
from moex_analyst.infrastructure.moex.parsing.mapper import map_marketdata
from moex_analyst.infrastructure.moex.parsing.parser import parse_block

if TYPE_CHECKING:
    from moex_analyst.infrastructure.moex.dto import QuoteDTO
    from moex_analyst.infrastructure.moex.transport.client import MoexHttpClient

__all__ = ["QuoteService"]


class QuoteService:
    """Fetches the current marketdata snapshot (price + volume) from ISS."""

    def __init__(self, client: MoexHttpClient) -> None:
        self._client = client

    async def get_quote(self, ticker: str) -> QuoteDTO:
        """Fetch the latest quote for one tracked instrument.

        Raises:
            KeyError: if ``ticker`` is not tracked.
            MoexEmptyDataError: if ISS returns no marketdata rows (e.g. the
                board is closed and reports nothing).
            MoexError: on transport/response failure.
        """
        ref = resolve_instrument(ticker)
        payload = await self._client.get_json(
            ref.marketdata_path,
            params={"iss.only": "marketdata"},
        )
        records = parse_block(payload, "marketdata")
        if not records:
            raise MoexEmptyDataError(f"No marketdata for {ticker}")
        # The board endpoint returns a single marketdata row for the security.
        return map_marketdata(records[0], ref)
