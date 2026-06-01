"""Pure message formatters: application DTOs -> Telegram HTML strings.

No aiogram, no I/O. Each function maps a value object to a ready-to-send HTML
message body, escaping all dynamic content. These are the layer's unit-tested
surface.
"""

from __future__ import annotations

from moex_analyst.presentation.bot.formatters.analysis import (
    format_alerts_block,
    format_instrument_analysis,
)
from moex_analyst.presentation.bot.formatters.market import (
    format_market_overview,
    format_ranking,
)
from moex_analyst.presentation.bot.formatters.misc import (
    format_error,
    format_help,
    format_start,
)
from moex_analyst.presentation.bot.formatters.watchlist import format_watchlist

__all__ = [
    "format_alerts_block",
    "format_error",
    "format_help",
    "format_instrument_analysis",
    "format_market_overview",
    "format_ranking",
    "format_start",
    "format_watchlist",
]
