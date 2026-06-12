from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from moex_analyst.presentation.bot.formatters import format_help, format_start
from moex_analyst.presentation.bot.keyboards import back_home_keyboard, main_menu_keyboard

__all__ = ["router"]

router = Router(name="start_help")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    first_name = message.from_user.first_name if message.from_user else None
    await message.answer(format_start(first_name), reply_markup=main_menu_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(format_help(), reply_markup=back_home_keyboard())
