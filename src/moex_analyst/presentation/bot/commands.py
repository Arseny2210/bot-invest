"""Telegram bot menu configuration.

Instead of exposing many slash commands (developer-oriented UX), we register
only a single menu button that returns users to the root interface.
Slash commands remain available internally as a fallback.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import BotCommand

if TYPE_CHECKING:
    from aiogram import Bot

__all__ = ["set_bot_menu"]

_BOT_COMMANDS: tuple[BotCommand, ...] = (
    BotCommand(command="start", description="🏠 Главное меню"),
)


async def set_bot_menu(bot: Bot) -> None:
    """Register a single menu entry that returns users to the main screen."""
    await bot.set_my_commands(list(_BOT_COMMANDS))
