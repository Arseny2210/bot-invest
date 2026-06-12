"""Handler for /analyze and the menu-driven analysis flow.

The menu flow uses FSM (4 steps): ticker ‣ timeframe ‣ analysis type ‣ result.
Every screen carries ⬅️ Назад and 🏠 Главное меню buttons.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka

from moex_analyst.application.use_cases import AnalyzeInstrumentUseCase
from moex_analyst.domain.market.timeframe import Timeframe
from moex_analyst.infrastructure.moex.config import INSTRUMENT_REGISTRY
from moex_analyst.presentation.bot.callbacks import (
    AnalyzeCallback,
    AnalyzeTypeCallback,
    MenuAction,
    MenuCallback,
    RefreshCallback,
    TickerCallback,
    TimeframeCallback,
)
from moex_analyst.presentation.bot.formatters import (
    format_error,
    format_instrument_analysis,
)
from moex_analyst.presentation.bot.formatters.text import fmt_instrument_name
from moex_analyst.presentation.bot.handlers._common import edit_or_answer as _edit_or_answer
from moex_analyst.presentation.bot.handlers.errors import friendly_error
from moex_analyst.presentation.bot.keyboards import (
    analysis_type_keyboard,
    main_menu_keyboard,
    result_keyboard,
    ticker_selection_keyboard,
    timeframe_keyboard,
)

__all__ = ["router"]

router = Router(name="analyze")


class AnalyzeFlow(StatesGroup):
    selecting_ticker = State()
    custom_ticker = State()
    selecting_timeframe = State()
    selecting_type = State()


_TIMEFRAME_MAP: dict[str, Timeframe] = {
    "15M": Timeframe.M15,
    "1H": Timeframe.H1,
    "4H": Timeframe.H4,
    "1D": Timeframe.D1,
    "1W": Timeframe.W1,
}

# Accept both "1H" (timeframe value) and "H1" (enum-name) spellings.
_TIMEFRAME_ALIASES: dict[str, Timeframe] = {
    "15M": Timeframe.M15,
    "1H": Timeframe.H1,
    "H1": Timeframe.H1,
    "4H": Timeframe.H4,
    "H4": Timeframe.H4,
    "1D": Timeframe.D1,
    "D1": Timeframe.D1,
    "DAY": Timeframe.D1,
    "1W": Timeframe.W1,
    "W1": Timeframe.W1,
    "WEEK": Timeframe.W1,
}


# ---------------------------------------------------------------------------
# /analyze command (free-text fallback)
# ---------------------------------------------------------------------------


def _parse_args(raw: str | None) -> tuple[str, Timeframe] | None:
    """Parse ``<ticker> [timeframe]``; return ``None`` if no ticker given."""
    if not raw or not raw.strip():
        return None
    parts = raw.split()
    ticker = parts[0].upper()
    timeframe = Timeframe.D1
    if len(parts) > 1:
        timeframe = _TIMEFRAME_ALIASES.get(parts[1].upper(), Timeframe.D1)
    return ticker, timeframe


@router.message(Command("analyze"))
async def cmd_analyze(
    message: Message,
    command: CommandObject,
    use_case: FromDishka[AnalyzeInstrumentUseCase],
    state: FSMContext,
) -> None:
    await state.clear()
    parsed = _parse_args(command.args)
    if parsed is None:
        await message.answer(
            format_error("Выберите инструмент через меню."),
        )
        return
    ticker, timeframe = parsed
    await _run_analysis(message, use_case, ticker, timeframe)


# ---------------------------------------------------------------------------
# Main menu → Analyze (start the flow)
# ---------------------------------------------------------------------------


@router.callback_query(MenuCallback.filter(F.action == MenuAction.ANALYZE))
async def cb_start_analyze(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await state.set_state(AnalyzeFlow.selecting_ticker)
    if isinstance(callback.message, Message):
        await _edit_or_answer(
            callback.message,
            "📈 <b>Анализ акции</b>\n\nВыберите инструмент:",
            reply_markup=ticker_selection_keyboard(),
        )
    await callback.answer()


# ---------------------------------------------------------------------------
# Custom ticker input
# ---------------------------------------------------------------------------


@router.callback_query(MenuCallback.filter(F.action == MenuAction.CUSTOM_TICKER))
async def cb_custom_ticker(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await state.set_state(AnalyzeFlow.custom_ticker)
    if isinstance(callback.message, Message):
        await _edit_or_answer(
            callback.message,
            "🔍 Введите тикер (например, <b>GAZP</b>):",
        )
    await callback.answer()


@router.message(StateFilter(AnalyzeFlow.custom_ticker))
async def msg_custom_ticker(
    message: Message,
    state: FSMContext,
    use_case: FromDishka[AnalyzeInstrumentUseCase],
) -> None:
    ticker = message.text.strip().upper() if message.text else ""
    if not ticker:
        await message.answer("Пожалуйста, введите тикер.")
        return
    if ticker not in INSTRUMENT_REGISTRY:
        await message.answer(
            format_error(f"Тикер <b>{ticker}</b> не найден."),
            reply_markup=ticker_selection_keyboard(),
        )
        await state.set_state(AnalyzeFlow.selecting_ticker)
        return
    await state.update_data(ticker=ticker)
    await state.set_state(AnalyzeFlow.selecting_timeframe)
    await message.answer(
        f"⏰ Выберите таймфрейм для <b>{fmt_instrument_name(ticker)}</b>:",
        reply_markup=timeframe_keyboard(),
    )


# ---------------------------------------------------------------------------
# Ticker selection
# ---------------------------------------------------------------------------


@router.callback_query(TickerCallback.filter())
async def cb_ticker(
    callback: CallbackQuery,
    callback_data: TickerCallback,
    state: FSMContext,
    use_case: FromDishka[AnalyzeInstrumentUseCase],
) -> None:
    ticker = callback_data.ticker
    await state.update_data(ticker=ticker)
    await state.set_state(AnalyzeFlow.selecting_timeframe)
    if isinstance(callback.message, Message):
        await _edit_or_answer(
            callback.message,
            f"⏰ Выберите таймфрейм для <b>{fmt_instrument_name(ticker)}</b>:",
            reply_markup=timeframe_keyboard(),
        )
    await callback.answer()


# ---------------------------------------------------------------------------
# Timeframe selection
# ---------------------------------------------------------------------------


@router.callback_query(TimeframeCallback.filter())
async def cb_timeframe(
    callback: CallbackQuery,
    callback_data: TimeframeCallback,
    state: FSMContext,
) -> None:
    tf = _TIMEFRAME_MAP.get(callback_data.value)
    if tf is None:
        await callback.answer("Некорректный таймфрейм", show_alert=True)
        return
    data = await state.get_data()
    ticker = data.get("ticker", "—")
    await state.update_data(timeframe=callback_data.value)
    await state.set_state(AnalyzeFlow.selecting_type)
    if isinstance(callback.message, Message):
        await _edit_or_answer(
            callback.message,
            f"📊 Выберите тип анализа для <b>"
            f"{fmt_instrument_name(ticker)} {callback_data.value}</b>:",
            reply_markup=analysis_type_keyboard(),
        )
    await callback.answer()


# ---------------------------------------------------------------------------
# Analysis type selection → run analysis
# ---------------------------------------------------------------------------


@router.callback_query(AnalyzeTypeCallback.filter())
async def cb_analysis_type(
    callback: CallbackQuery,
    callback_data: AnalyzeTypeCallback,
    state: FSMContext,
    use_case: FromDishka[AnalyzeInstrumentUseCase],
) -> None:
    if callback_data.type_ != "full":
        await callback.answer("Некорректный тип анализа", show_alert=True)
        return
    data = await state.get_data()
    ticker: str = data.get("ticker", "")
    tf_value: str = data.get("timeframe", "1D")
    timeframe = _TIMEFRAME_MAP.get(tf_value, Timeframe.D1)

    await state.set_state(AnalyzeFlow.selecting_type)
    if isinstance(callback.message, Message):
        await _run_analysis(callback.message, use_case, ticker, timeframe, edit=True)
    await callback.answer()


# ---------------------------------------------------------------------------
# Watchlist quick-access callback (legacy)
# ---------------------------------------------------------------------------


@router.callback_query(AnalyzeCallback.filter())
async def cb_analyze(
    callback: CallbackQuery,
    callback_data: AnalyzeCallback,
    use_case: FromDishka[AnalyzeInstrumentUseCase],
    state: FSMContext,
) -> None:
    await state.clear()
    if isinstance(callback.message, Message):
        await _run_analysis(
            callback.message, use_case, callback_data.ticker, Timeframe.D1, edit=True
        )
    await callback.answer()


# ---------------------------------------------------------------------------
# Refresh analysis (Part 7)
# ---------------------------------------------------------------------------


@router.callback_query(RefreshCallback.filter())
async def cb_refresh_analysis(
    callback: CallbackQuery,
    callback_data: RefreshCallback,
    use_case: FromDishka[AnalyzeInstrumentUseCase],
) -> None:
    ticker = callback_data.ticker
    tf_value = callback_data.tf_value
    timeframe = _TIMEFRAME_MAP.get(tf_value, Timeframe.D1)
    if isinstance(callback.message, Message):
        await _run_analysis(callback.message, use_case, ticker, timeframe, edit=True)
    await callback.answer()


# ---------------------------------------------------------------------------
# Back / Main menu navigation
# ---------------------------------------------------------------------------


@router.callback_query(MenuCallback.filter(F.action == MenuAction.BACK))
async def cb_back(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    current = await state.get_state()
    target = None
    if current == AnalyzeFlow.selecting_ticker.state:
        await state.clear()
        if isinstance(callback.message, Message):
            await _edit_or_answer(
                callback.message,
                "Главное меню",
                reply_markup=main_menu_keyboard(),
            )
        await callback.answer()
        return
    if current == AnalyzeFlow.selecting_timeframe.state:
        await state.set_state(AnalyzeFlow.selecting_ticker)
        target = ticker_selection_keyboard()
        text = "📈 <b>Анализ акции</b>\n\nВыберите инструмент:"
    elif current == AnalyzeFlow.selecting_type.state:
        data = await state.get_data()
        ticker = data.get("ticker", "—")
        await state.set_state(AnalyzeFlow.selecting_timeframe)
        target = timeframe_keyboard()
        text = f"⏰ Выберите таймфрейм для <b>{fmt_instrument_name(ticker)}</b>:"
    else:
        await state.clear()
        if isinstance(callback.message, Message):
            await _edit_or_answer(
                callback.message,
                "Главное меню",
                reply_markup=main_menu_keyboard(),
            )
        await callback.answer()
        return

    if isinstance(callback.message, Message):
        await _edit_or_answer(callback.message, text, reply_markup=target)
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.action == MenuAction.MAIN_MENU))
async def cb_main_menu(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await state.clear()
    if isinstance(callback.message, Message):
        await _edit_or_answer(
            callback.message,
            "Главное меню",
            reply_markup=main_menu_keyboard(),
        )
    await callback.answer()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _run_analysis(
    message: Message,
    use_case: AnalyzeInstrumentUseCase,
    ticker: str,
    timeframe: Timeframe,
    edit: bool = False,
) -> None:
    try:
        report = await use_case.execute(ticker, timeframe)
    except Exception as exc:
        if edit:
            await _edit_or_answer(message, friendly_error(exc))
        else:
            await message.answer(friendly_error(exc))
        return
    text = format_instrument_analysis(report)
    tf_value = timeframe.value
    reply = result_keyboard(ticker=ticker, tf_value=tf_value)
    if edit:
        await _edit_or_answer(message, text, reply_markup=reply)
    else:
        await message.answer(text, reply_markup=reply)
