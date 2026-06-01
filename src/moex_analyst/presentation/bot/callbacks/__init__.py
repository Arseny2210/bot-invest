"""Typed callback-data factories for inline keyboards.

Aiogram ``CallbackData`` subclasses give structured, validated callback payloads
(``analyze:SNGS``, ``menu:best``) instead of ad-hoc string parsing.
"""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData

__all__ = ["AnalyzeCallback", "MenuAction", "MenuCallback"]

from enum import StrEnum


class MenuAction(StrEnum):
    """Actions reachable from the main inline menu."""

    MARKET = "market"
    BEST = "best"
    WORST = "worst"
    WATCHLIST = "watchlist"
    HELP = "help"


class MenuCallback(CallbackData, prefix="menu"):
    """Main-menu button -> a top-level action."""

    action: MenuAction


class AnalyzeCallback(CallbackData, prefix="analyze"):
    """Watchlist button -> analyse a specific ticker."""

    ticker: str
