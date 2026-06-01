"""Inline keyboard builders for the bot."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.utils.keyboard import InlineKeyboardBuilder

from moex_analyst.presentation.bot.callbacks import (
    AnalyzeCallback,
    MenuAction,
    MenuCallback,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from aiogram.types import InlineKeyboardMarkup

__all__ = ["main_menu_keyboard", "watchlist_keyboard"]

_MENU_BUTTONS: tuple[tuple[str, MenuAction], ...] = (
    ("🗺 Market", MenuAction.MARKET),
    ("🏆 Best", MenuAction.BEST),
    ("🐻 Worst", MenuAction.WORST),
    ("⭐ Watchlist", MenuAction.WATCHLIST),
    ("🛟 Help", MenuAction.HELP),
)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """The main inline menu shown on /start."""
    builder = InlineKeyboardBuilder()
    for label, action in _MENU_BUTTONS:
        builder.button(text=label, callback_data=MenuCallback(action=action))
    builder.adjust(3, 2)
    return builder.as_markup()


def watchlist_keyboard(tickers: Iterable[str]) -> InlineKeyboardMarkup:
    """One button per tracked ticker -> analyse it."""
    builder = InlineKeyboardBuilder()
    for ticker in tickers:
        builder.button(text=ticker, callback_data=AnalyzeCallback(ticker=ticker))
    builder.adjust(3)
    return builder.as_markup()
