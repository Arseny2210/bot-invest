from unittest.mock import AsyncMock, MagicMock

from aiogram.types import Message

from moex_analyst.presentation.bot.handlers.start_help import cmd_help, cmd_start


class TestCmdStart:
    async def test_sends_start_message(self, mock_message: MagicMock) -> None:
        await cmd_start(mock_message)

        mock_message.answer.assert_awaited_once()
        text = mock_message.answer.call_args[0][0]
        assert "MOEX Analyst" in text
        assert "Привет, TestUser!" in text

    async def test_includes_main_menu_keyboard(self, mock_message: MagicMock) -> None:
        await cmd_start(mock_message)

        kwargs = mock_message.answer.call_args.kwargs
        assert "reply_markup" in kwargs

    async def test_handles_no_first_name(self) -> None:
        msg = MagicMock(spec=Message)
        msg.from_user = None
        msg.answer = AsyncMock()

        await cmd_start(msg)

        text = msg.answer.call_args[0][0]
        assert "Привет!" in text


class TestCmdHelp:
    async def test_sends_help_message(self, mock_message: MagicMock) -> None:
        await cmd_help(mock_message)

        mock_message.answer.assert_awaited_once()
        text = mock_message.answer.call_args[0][0]
        assert "Разделы" in text
        assert "Анализ акции" in text

    async def test_includes_main_menu_keyboard(self, mock_message: MagicMock) -> None:
        await cmd_help(mock_message)

        kwargs = mock_message.answer.call_args.kwargs
        assert "reply_markup" in kwargs
