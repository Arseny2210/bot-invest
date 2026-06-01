"""The Telegram command menu shown in clients (the ``/`` autocomplete list)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import BotCommand

if TYPE_CHECKING:
    from aiogram import Bot

__all__ = ["BOT_COMMANDS", "set_bot_commands"]

BOT_COMMANDS: tuple[BotCommand, ...] = (
    BotCommand(command="analyze", description="Analyse an instrument (/analyze SNGS)"),
    BotCommand(command="market", description="Ranked market overview"),
    BotCommand(command="best", description="Most bullish instruments"),
    BotCommand(command="worst", description="Most bearish instruments"),
    BotCommand(command="watchlist", description="Tracked instruments"),
    BotCommand(command="help", description="Show help"),
)


async def set_bot_commands(bot: Bot) -> None:
    """Register the command menu with Telegram."""
    await bot.set_my_commands(list(BOT_COMMANDS))
