from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka

from moex_analyst.application.use_cases import MarketOverviewUseCase
from moex_analyst.presentation.bot.formatters import format_signals
from moex_analyst.presentation.bot.handlers.errors import friendly_error
from moex_analyst.presentation.bot.keyboards import signals_keyboard

__all__ = ["router"]

router = Router(name="signals")


@router.message(Command("signals"))
async def cmd_signals(
    message: Message,
    use_case: FromDishka[MarketOverviewUseCase],
) -> None:
    await _send_signals(message, use_case)


async def send_signals_from_callback(
    target: Message,
    use_case: FromDishka[MarketOverviewUseCase],
) -> None:
    await _send_signals(target, use_case)


async def _send_signals(
    message: Message,
    use_case: MarketOverviewUseCase,
) -> None:
    try:
        overview = await use_case.execute()
    except Exception as exc:
        await message.answer(friendly_error(exc))
        return
    await message.answer(
        format_signals(overview),
        reply_markup=signals_keyboard(),
    )
