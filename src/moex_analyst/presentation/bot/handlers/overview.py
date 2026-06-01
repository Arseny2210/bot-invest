"""Handlers for /market, /best, /worst, /watchlist and the main-menu callbacks."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka

from moex_analyst.application.use_cases import (
    MarketOverviewUseCase,
    WatchlistUseCase,
)
from moex_analyst.application.use_cases._common import tracked_tickers
from moex_analyst.presentation.bot.callbacks import MenuAction, MenuCallback
from moex_analyst.presentation.bot.formatters import (
    format_help,
    format_market_overview,
    format_ranking,
    format_watchlist,
)
from moex_analyst.presentation.bot.handlers.errors import friendly_error
from moex_analyst.presentation.bot.keyboards import watchlist_keyboard

__all__ = ["router"]

router = Router(name="overview")


# --- command handlers -------------------------------------------------------
@router.message(Command("market"))
async def cmd_market(message: Message, use_case: FromDishka[MarketOverviewUseCase]) -> None:
    await _send_overview(message, use_case, MenuAction.MARKET)


@router.message(Command("best"))
async def cmd_best(message: Message, use_case: FromDishka[MarketOverviewUseCase]) -> None:
    await _send_overview(message, use_case, MenuAction.BEST)


@router.message(Command("worst"))
async def cmd_worst(message: Message, use_case: FromDishka[MarketOverviewUseCase]) -> None:
    await _send_overview(message, use_case, MenuAction.WORST)


@router.message(Command("watchlist"))
async def cmd_watchlist(message: Message, use_case: FromDishka[WatchlistUseCase]) -> None:
    await _send_watchlist(message, use_case)


# --- main-menu callback -----------------------------------------------------
@router.callback_query(MenuCallback.filter())
async def cb_menu(
    callback: CallbackQuery,
    callback_data: MenuCallback,
    market_use_case: FromDishka[MarketOverviewUseCase],
    watchlist_use_case: FromDishka[WatchlistUseCase],
) -> None:
    target = callback.message if isinstance(callback.message, Message) else None
    if target is not None:
        action = callback_data.action
        if action is MenuAction.HELP:
            await target.answer(format_help())
        elif action is MenuAction.WATCHLIST:
            await _send_watchlist(target, watchlist_use_case)
        else:
            await _send_overview(target, market_use_case, action)
    await callback.answer()


# --- shared senders ---------------------------------------------------------
async def _send_overview(
    message: Message,
    use_case: MarketOverviewUseCase,
    action: MenuAction,
) -> None:
    try:
        overview = await use_case.execute()
    except Exception as exc:  # mapped to a friendly user message
        await message.answer(friendly_error(exc))
        return

    if action is MenuAction.BEST:
        text = format_ranking(overview, best=True)
    elif action is MenuAction.WORST:
        text = format_ranking(overview, best=False)
    else:
        text = format_market_overview(overview)
    await message.answer(text)


async def _send_watchlist(message: Message, use_case: WatchlistUseCase) -> None:
    watchlist = await use_case.execute()
    await message.answer(
        format_watchlist(watchlist),
        reply_markup=watchlist_keyboard(tracked_tickers()),
    )
