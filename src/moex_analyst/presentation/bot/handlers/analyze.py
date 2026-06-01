"""Handler for /analyze and the watchlist analyse callbacks."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka

from moex_analyst.application.use_cases import AnalyzeInstrumentUseCase
from moex_analyst.domain.market.timeframe import Timeframe
from moex_analyst.presentation.bot.callbacks import AnalyzeCallback
from moex_analyst.presentation.bot.formatters import (
    format_error,
    format_instrument_analysis,
)
from moex_analyst.presentation.bot.handlers.errors import friendly_error

__all__ = ["router"]

router = Router(name="analyze")

# Accept both "1H" (timeframe value) and "H1" (enum-name) spellings.
_TIMEFRAME_ALIASES: dict[str, Timeframe] = {
    "1H": Timeframe.H1, "H1": Timeframe.H1,
    "4H": Timeframe.H4, "H4": Timeframe.H4,
    "1D": Timeframe.D1, "D1": Timeframe.D1, "DAY": Timeframe.D1,
}


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
) -> None:
    parsed = _parse_args(command.args)
    if parsed is None:
        await message.answer(
            format_error("Usage: /analyze <ticker> [1H|4H|1D]. Example: /analyze SNGS"),
        )
        return
    ticker, timeframe = parsed
    await _run_analysis(message, use_case, ticker, timeframe)


@router.callback_query(AnalyzeCallback.filter())
async def cb_analyze(
    callback: CallbackQuery,
    callback_data: AnalyzeCallback,
    use_case: FromDishka[AnalyzeInstrumentUseCase],
) -> None:
    if isinstance(callback.message, Message):
        await _run_analysis(callback.message, use_case, callback_data.ticker, Timeframe.D1)
    await callback.answer()


async def _run_analysis(
    message: Message,
    use_case: AnalyzeInstrumentUseCase,
    ticker: str,
    timeframe: Timeframe,
) -> None:
    try:
        report = await use_case.execute(ticker, timeframe)
    except Exception as exc:  # mapped to a friendly user message
        await message.answer(friendly_error(exc))
        return
    await message.answer(format_instrument_analysis(report))
