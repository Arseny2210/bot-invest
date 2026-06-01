"""Parser for the MOEX ISS response envelope.

ISS returns each logical table as ``{"columns": [...], "data": [[...], ...]}``.
This module turns a named block into a list of column→value dicts, isolating
that quirky shape so services and mappers work with ordinary records.
"""

from __future__ import annotations

from typing import Any

from moex_analyst.infrastructure.moex.errors import MoexResponseError

__all__ = ["parse_block"]


def parse_block(payload: Any, block: str) -> list[dict[str, Any]]:
    """Extract one ISS block as a list of records.

    Args:
        payload: the decoded JSON response (expected to be a mapping).
        block: the block name, e.g. ``"candles"``, ``"securities"``,
            ``"marketdata"``, ``"description"``.

    Returns:
        One dict per data row, keyed by the block's column names. An empty list
        if the block exists but has no rows.

    Raises:
        MoexResponseError: if the payload or block is not shaped as expected.
    """
    if not isinstance(payload, dict):
        raise MoexResponseError(f"Expected JSON object, got {type(payload).__name__}")

    raw_block = payload.get(block)
    if raw_block is None:
        raise MoexResponseError(f"ISS response has no '{block}' block")
    if not isinstance(raw_block, dict):
        raise MoexResponseError(f"ISS block '{block}' is not an object")

    columns = raw_block.get("columns")
    data = raw_block.get("data")
    if not isinstance(columns, list) or not isinstance(data, list):
        raise MoexResponseError(f"ISS block '{block}' missing columns/data arrays")

    records: list[dict[str, Any]] = []
    for row in data:
        if not isinstance(row, list) or len(row) != len(columns):
            raise MoexResponseError(
                f"ISS block '{block}' row width {len(row) if isinstance(row, list) else '?'}"
                f" != columns width {len(columns)}",
            )
        records.append(dict(zip(columns, row, strict=True)))
    return records
