"""Instrument metadata service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from moex_analyst.infrastructure.moex.config import resolve_instrument
from moex_analyst.infrastructure.moex.errors import MoexEmptyDataError
from moex_analyst.infrastructure.moex.parsing.mapper import map_description
from moex_analyst.infrastructure.moex.parsing.parser import parse_block

if TYPE_CHECKING:
    from moex_analyst.infrastructure.moex.dto import InstrumentDTO
    from moex_analyst.infrastructure.moex.transport.client import MoexHttpClient

__all__ = ["InstrumentService"]


class InstrumentService:
    """Fetches static metadata for tracked instruments from ISS."""

    def __init__(self, client: MoexHttpClient) -> None:
        self._client = client

    async def get_instrument(self, ticker: str) -> InstrumentDTO:
        """Fetch metadata for one tracked instrument by platform ticker.

        Raises:
            KeyError: if ``ticker`` is not tracked.
            MoexEmptyDataError: if ISS returns no description rows.
            MoexError: on transport/response failure.
        """
        ref = resolve_instrument(ticker)
        payload = await self._client.get_json(
            ref.description_path,
            params={"iss.only": "description"},
        )
        records = parse_block(payload, "description")
        if not records:
            raise MoexEmptyDataError(f"No description data for {ticker}")
        return map_description(records, ref)
