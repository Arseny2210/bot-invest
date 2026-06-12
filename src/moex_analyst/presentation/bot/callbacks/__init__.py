from __future__ import annotations

from enum import StrEnum

from aiogram.filters.callback_data import CallbackData

__all__ = [
    "AnalyzeCallback",
    "AnalyzeTypeCallback",
    "MarketRefreshCallback",
    "MenuAction",
    "MenuCallback",
    "RefreshAction",
    "RefreshCallback",
    "TickerCallback",
    "TimeframeCallback",
]


class MenuAction(StrEnum):
    MAIN_MENU = "main_menu"
    BACK = "back"
    MARKET = "market"
    BEST = "best"
    WORST = "worst"
    WATCHLIST = "watchlist"
    HELP = "help"
    SIGNALS = "signals"
    STATISTICS = "statistics"
    SETTINGS = "settings"
    ANALYZE = "analyze"
    CUSTOM_TICKER = "custom_ticker"


class MenuCallback(CallbackData, prefix="menu"):
    action: MenuAction


class TickerCallback(CallbackData, prefix="ticker"):
    ticker: str


class TimeframeCallback(CallbackData, prefix="tf"):
    value: str


class AnalyzeTypeCallback(CallbackData, prefix="atype"):
    type_: str


class AnalyzeCallback(CallbackData, prefix="analyze"):
    ticker: str


class RefreshAction(StrEnum):
    MARKET = "market"
    SIGNALS = "signals"


class RefreshCallback(CallbackData, prefix="refresh"):
    ticker: str
    tf_value: str


class MarketRefreshCallback(CallbackData, prefix="mkt_refresh"):
    action: RefreshAction
