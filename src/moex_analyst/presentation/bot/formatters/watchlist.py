"""Formatter for ``/watchlist`` — the tracked-instrument list."""

from __future__ import annotations

from typing import TYPE_CHECKING

from moex_analyst.presentation.bot.formatters.text import escape

if TYPE_CHECKING:
    from moex_analyst.application.use_cases.dto import Watchlist

__all__ = ["format_watchlist"]

_MARKET_ICONS = {"index": "📐", "shares": "🏢"}


def format_watchlist(watchlist: Watchlist) -> str:
    """Render the tracked instruments and a hint on analysing one."""
    header = "⭐ <b>Watchlist</b> <i>(tracked instruments)</i>"
    if not watchlist.instruments:
        return f"{header}\n\n— empty —"

    rows = [
        f"• {_MARKET_ICONS.get(inst.market_type.value, '•')} "
        f"<b>{escape(inst.ticker)}</b> <i>({escape(inst.secid)})</i>"
        for inst in watchlist.instruments
    ]
    hint = "\n<i>Tap a button below or send /analyze &lt;ticker&gt;.</i>"
    return "\n".join([header, "", *rows, hint])
