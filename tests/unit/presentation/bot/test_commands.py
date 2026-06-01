from unittest.mock import AsyncMock, MagicMock

from aiogram import Bot
from aiogram.types import BotCommand

from moex_analyst.presentation.bot.commands import BOT_COMMANDS, set_bot_commands


class TestBotCommands:
    def test_has_six_commands(self) -> None:
        assert len(BOT_COMMANDS) == 6

    def test_each_is_bot_command(self) -> None:
        for cmd in BOT_COMMANDS:
            assert isinstance(cmd, BotCommand)
            assert cmd.command
            assert cmd.description

    def test_analyze_command_present(self) -> None:
        commands = {c.command for c in BOT_COMMANDS}
        for expected in ("analyze", "market", "best", "worst", "watchlist", "help"):
            assert expected in commands

    def test_analyze_description_includes_example(self) -> None:
        analyze = next(c for c in BOT_COMMANDS if c.command == "analyze")
        assert "/analyze" in analyze.description


class TestSetBotCommands:
    async def test_calls_set_my_commands_with_list(self) -> None:
        bot = MagicMock(spec=Bot)
        bot.set_my_commands = AsyncMock()

        await set_bot_commands(bot)

        bot.set_my_commands.assert_awaited_once()
        args, _ = bot.set_my_commands.call_args
        commands_list = args[0]
        assert len(commands_list) == 6
        assert all(isinstance(c, BotCommand) for c in commands_list)

    async def test_commands_match_bot_commands_constant(self) -> None:
        bot = MagicMock(spec=Bot)
        bot.set_my_commands = AsyncMock()

        await set_bot_commands(bot)

        args, _ = bot.set_my_commands.call_args
        assert args[0] == list(BOT_COMMANDS)
