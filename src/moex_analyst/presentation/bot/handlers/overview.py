from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka

from moex_analyst.application.services import ForecastTrackingService
from moex_analyst.application.use_cases import (
    MarketOverviewUseCase,
    WatchlistUseCase,
)
from moex_analyst.application.use_cases._common import tracked_tickers
from moex_analyst.core.settings import Settings
from moex_analyst.presentation.bot.callbacks import (
    MarketRefreshCallback,
    MenuAction,
    MenuCallback,
    RefreshAction,
)
from moex_analyst.presentation.bot.formatters import (
    format_help,
    format_market_overview,
    format_ranking,
    format_settings,
    format_signals,
    format_statistics,
    format_watchlist,
)
from moex_analyst.presentation.bot.handlers._common import edit_or_answer as _edit_or_answer
from moex_analyst.presentation.bot.handlers.errors import friendly_error
from moex_analyst.presentation.bot.keyboards import (
    back_home_keyboard,
    main_menu_keyboard,
    overview_keyboard,
    signals_keyboard,
    watchlist_keyboard,
)

__all__ = ["router"]

router = Router(name="overview")


@router.message(Command("market"))
async def cmd_market(
    message: Message,
    use_case: FromDishka[MarketOverviewUseCase],
) -> None:
    await _send_overview(message, use_case, MenuAction.MARKET)


@router.message(Command("best"))
async def cmd_best(
    message: Message,
    use_case: FromDishka[MarketOverviewUseCase],
) -> None:
    await _send_overview(message, use_case, MenuAction.BEST)


@router.message(Command("worst"))
async def cmd_worst(
    message: Message,
    use_case: FromDishka[MarketOverviewUseCase],
) -> None:
    await _send_overview(message, use_case, MenuAction.WORST)


@router.message(Command("watchlist"))
async def cmd_watchlist(
    message: Message,
    use_case: FromDishka[WatchlistUseCase],
) -> None:
    await _send_watchlist(message, use_case)


@router.callback_query(MenuCallback.filter())
async def cb_menu(
    callback: CallbackQuery,
    callback_data: MenuCallback,
    market_use_case: FromDishka[MarketOverviewUseCase],
    watchlist_use_case: FromDishka[WatchlistUseCase],
    forecast_service: FromDishka[ForecastTrackingService],
    settings: FromDishka[Settings],
    state: FSMContext,
) -> None:
    target = callback.message if isinstance(callback.message, Message) else None
    if target is None:
        await callback.answer()
        return

    action = callback_data.action

    if action is MenuAction.MAIN_MENU:
        await state.clear()
        await _edit_or_answer(
            target,
            "Главное меню",
            reply_markup=main_menu_keyboard(),
        )
    elif action is MenuAction.HELP:
        await _edit_or_answer(
            target,
            format_help(),
            reply_markup=back_home_keyboard(),
        )
    elif action is MenuAction.WATCHLIST:
        await _send_watchlist(target, watchlist_use_case, edit=True)
    elif action is MenuAction.SIGNALS:
        await _send_signals(target, market_use_case, edit=True)
    elif action is MenuAction.STATISTICS:
        await _send_statistics(target, forecast_service, edit=True)
    elif action is MenuAction.SETTINGS:
        await _send_settings(target, settings, edit=True)
    elif action is MenuAction.ANALYZE:
        pass  # handled by analyze.router
    else:
        await _send_overview(target, market_use_case, action, edit=True)

    await callback.answer()


# ---------------------------------------------------------------------------
# Market / Signals refresh (Part 7)
# ---------------------------------------------------------------------------


@router.callback_query(MarketRefreshCallback.filter(F.action == RefreshAction.MARKET))
async def cb_refresh_market(
    callback: CallbackQuery,
    use_case: FromDishka[MarketOverviewUseCase],
) -> None:
    if isinstance(callback.message, Message):
        await _send_overview(callback.message, use_case, MenuAction.MARKET, edit=True)
    await callback.answer()


@router.callback_query(MarketRefreshCallback.filter(F.action == RefreshAction.SIGNALS))
async def cb_refresh_signals(
    callback: CallbackQuery,
    use_case: FromDishka[MarketOverviewUseCase],
) -> None:
    if isinstance(callback.message, Message):
        await _send_signals(callback.message, use_case, edit=True)
    await callback.answer()


async def _send_overview(
    message: Message,
    use_case: MarketOverviewUseCase,
    action: MenuAction,
    edit: bool = False,
) -> None:
    try:
        overview = await use_case.execute()
    except Exception as exc:
        text = friendly_error(exc)
        if edit:
            await _edit_or_answer(message, text)
        else:
            await message.answer(text)
        return
    if action is MenuAction.BEST:
        text = format_ranking(overview, best=True)
        reply = back_home_keyboard()
    elif action is MenuAction.WORST:
        text = format_ranking(overview, best=False)
        reply = back_home_keyboard()
    else:
        text = format_market_overview(overview)
        reply = overview_keyboard()
    if edit:
        await _edit_or_answer(message, text, reply_markup=reply)
    else:
        await message.answer(text, reply_markup=reply)


async def _send_watchlist(
    message: Message,
    use_case: WatchlistUseCase,
    edit: bool = False,
) -> None:
    watchlist = await use_case.execute()
    text = format_watchlist(watchlist)
    reply_markup = watchlist_keyboard(tracked_tickers())
    if edit:
        await _edit_or_answer(message, text, reply_markup=reply_markup)
    else:
        await message.answer(text, reply_markup=reply_markup)


async def _send_signals(
    message: Message,
    use_case: MarketOverviewUseCase,
    edit: bool = False,
) -> None:
    try:
        overview = await use_case.execute()
    except Exception as exc:
        text = friendly_error(exc)
        if edit:
            await _edit_or_answer(message, text)
        else:
            await message.answer(text)
        return
    text = format_signals(overview)
    if edit:
        await _edit_or_answer(message, text, reply_markup=signals_keyboard())
    else:
        await message.answer(text, reply_markup=signals_keyboard())


async def _send_statistics(
    message: Message,
    forecast_service: ForecastTrackingService,
    edit: bool = False,
) -> None:
    try:
        metrics = await forecast_service.calculate_metrics()
    except Exception:
        metrics = None
    text = format_statistics(metrics)
    if edit:
        await _edit_or_answer(message, text, reply_markup=back_home_keyboard())
    else:
        await message.answer(text, reply_markup=back_home_keyboard())


async def _send_settings(
    message: Message,
    cfg: Settings,
    edit: bool = False,
) -> None:
    text = format_settings(cfg)
    if edit:
        await _edit_or_answer(message, text, reply_markup=back_home_keyboard())
    else:
        await message.answer(text, reply_markup=back_home_keyboard())
