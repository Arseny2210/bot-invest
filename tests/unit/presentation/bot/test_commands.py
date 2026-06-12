from unittest.mock import AsyncMock, MagicMock

from aiogram import Bot
from aiogram.types import BotCommand

from moex_analyst.presentation.bot.commands import set_bot_menu


class TestSetBotMenu:
    async def test_calls_set_my_commands_with_single_entry(self) -> None:
        bot = MagicMock(spec=Bot)
        bot.set_my_commands = AsyncMock()

        await set_bot_menu(bot)

        bot.set_my_commands.assert_awaited_once()
        args, _ = bot.set_my_commands.call_args
        commands_list = args[0]
        assert len(commands_list) == 1
        assert all(isinstance(c, BotCommand) for c in commands_list)

    async def test_sets_start_as_home_menu(self) -> None:
        bot = MagicMock(spec=Bot)
        bot.set_my_commands = AsyncMock()

        await set_bot_menu(bot)

        args, _ = bot.set_my_commands.call_args
        cmd = args[0][0]
        assert cmd.command == "start"
        assert "Главное меню" in cmd.description
