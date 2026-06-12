from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka

from moex_analyst.core.settings import Settings
from moex_analyst.presentation.bot.formatters import format_settings
from moex_analyst.presentation.bot.keyboards import back_home_keyboard

__all__ = ["router"]

router = Router(name="settings")


@router.message(Command("settings"))
async def cmd_settings(
    message: Message,
    settings: FromDishka[Settings],
) -> None:
    await _send_settings(message, settings)


async def send_settings_from_callback(
    target: Message,
    settings: Settings,
) -> None:
    await _send_settings(target, settings)


async def _send_settings(
    message: Message,
    cfg: Settings,
) -> None:
    await message.answer(
        format_settings(cfg),
        reply_markup=back_home_keyboard(),
    )
