from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.utils.keyboard import InlineKeyboardBuilder

from moex_analyst.presentation.bot.callbacks import (
    AnalyzeCallback,
    AnalyzeTypeCallback,
    MarketRefreshCallback,
    MenuAction,
    MenuCallback,
    RefreshAction,
    RefreshCallback,
    TickerCallback,
    TimeframeCallback,
)
from moex_analyst.presentation.bot.formatters.text import fmt_instrument_menu, fmt_instrument_name

if TYPE_CHECKING:
    from collections.abc import Iterable

    from aiogram.types import InlineKeyboardMarkup

__all__ = [
    "analysis_type_keyboard",
    "back_home_keyboard",
    "main_menu_keyboard",
    "overview_keyboard",
    "result_keyboard",
    "signals_keyboard",
    "ticker_selection_keyboard",
    "timeframe_keyboard",
    "watchlist_keyboard",
]

_MENU_BUTTONS: tuple[tuple[str, MenuAction], ...] = (
    ("📈 Анализ акции", MenuAction.ANALYZE),
    ("📊 Состояние рынка", MenuAction.MARKET),
    ("⭐ Избранное", MenuAction.WATCHLIST),
    ("🎯 Сигналы", MenuAction.SIGNALS),
    ("📋 Статистика", MenuAction.STATISTICS),
    ("⚙️ Настройки", MenuAction.SETTINGS),
    ("❓ Помощь", MenuAction.HELP),
)

_TICKER_LIST = ("IMOEX", "UWGN", "SNGS", "VTBR", "SGZH", "IRKT")

_TIMEFRAME_LIST = ("15M", "1H", "4H", "1D", "1W")


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, action in _MENU_BUTTONS:
        builder.button(text=label, callback_data=MenuCallback(action=action))
    builder.adjust(3, 3, 1)
    return builder.as_markup()


def back_home_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data=MenuCallback(action=MenuAction.MAIN_MENU))
    builder.button(text="🏠 Главное меню", callback_data=MenuCallback(action=MenuAction.MAIN_MENU))
    builder.adjust(2)
    return builder.as_markup()


def ticker_selection_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for t in _TICKER_LIST:
        builder.button(text=fmt_instrument_menu(t), callback_data=TickerCallback(ticker=t))
    builder.button(
        text="🔍 Ввести свой тикер",
        callback_data=MenuCallback(action=MenuAction.CUSTOM_TICKER),
    )
    builder.button(text="⬅️ Назад", callback_data=MenuCallback(action=MenuAction.MAIN_MENU))
    builder.button(text="🏠 Главное меню", callback_data=MenuCallback(action=MenuAction.MAIN_MENU))
    builder.adjust(2, 2, 2, 1, 2)
    return builder.as_markup()


def timeframe_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for tf in _TIMEFRAME_LIST:
        builder.button(text=tf, callback_data=TimeframeCallback(value=tf))
    builder.button(text="⬅️ Назад", callback_data=MenuCallback(action=MenuAction.BACK))
    builder.button(text="🏠 Главное меню", callback_data=MenuCallback(action=MenuAction.MAIN_MENU))
    builder.adjust(3, 2, 2)
    return builder.as_markup()


def analysis_type_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📊 Полный анализ",
        callback_data=AnalyzeTypeCallback(type_="full"),
    )
    builder.button(text="⬅️ Назад", callback_data=MenuCallback(action=MenuAction.BACK))
    builder.button(text="🏠 Главное меню", callback_data=MenuCallback(action=MenuAction.MAIN_MENU))
    builder.adjust(1, 2)
    return builder.as_markup()


def result_keyboard(ticker: str = "", tf_value: str = "") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if ticker and tf_value:
        builder.button(
            text="🔄 Обновить данные",
            callback_data=RefreshCallback(ticker=ticker, tf_value=tf_value),
        )
    builder.button(text="⬅️ Назад", callback_data=MenuCallback(action=MenuAction.BACK))
    builder.button(text="🏠 Главное меню", callback_data=MenuCallback(action=MenuAction.MAIN_MENU))
    builder.adjust(1 if ticker and tf_value else 2)
    return builder.as_markup()


def overview_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔄 Обновить рынок",
        callback_data=MarketRefreshCallback(action=RefreshAction.MARKET),
    )
    builder.button(text="⬅️ Назад", callback_data=MenuCallback(action=MenuAction.MAIN_MENU))
    builder.button(text="🏠 Главное меню", callback_data=MenuCallback(action=MenuAction.MAIN_MENU))
    builder.adjust(1, 2)
    return builder.as_markup()


def signals_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔄 Обновить сигналы",
        callback_data=MarketRefreshCallback(action=RefreshAction.SIGNALS),
    )
    builder.button(text="⬅️ Назад", callback_data=MenuCallback(action=MenuAction.MAIN_MENU))
    builder.button(text="🏠 Главное меню", callback_data=MenuCallback(action=MenuAction.MAIN_MENU))
    builder.adjust(1, 2)
    return builder.as_markup()


def watchlist_keyboard(tickers: Iterable[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ticker in tickers:
        builder.button(
            text=fmt_instrument_name(ticker), callback_data=AnalyzeCallback(ticker=ticker)
        )
    builder.button(text="⬅️ Назад", callback_data=MenuCallback(action=MenuAction.MAIN_MENU))
    builder.button(text="🏠 Главное меню", callback_data=MenuCallback(action=MenuAction.MAIN_MENU))
    builder.adjust(3, 2)
    return builder.as_markup()
