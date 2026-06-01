from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import CallbackQuery, Message, TelegramObject

from moex_analyst.presentation.bot.middlewares.logging import (
    LoggingMiddleware,
    _describe,
)


class TestDescribe:
    def test_message_with_text(self) -> None:
        msg = MagicMock(spec=Message)
        msg.from_user = MagicMock()
        msg.from_user.id = 42
        msg.text = "hello"
        user_id, payload = _describe(msg)
        assert user_id == 42
        assert payload == "hello"

    def test_message_without_text(self) -> None:
        msg = MagicMock(spec=Message)
        msg.from_user = MagicMock()
        msg.from_user.id = 42
        msg.text = None
        user_id, payload = _describe(msg)
        assert user_id == 42
        assert payload == "<non-text>"

    def test_message_without_user(self) -> None:
        msg = MagicMock(spec=Message)
        msg.from_user = None
        msg.text = "/start"
        user_id, payload = _describe(msg)
        assert user_id is None
        assert payload == "/start"

    def test_callback_query(self) -> None:
        cb = MagicMock(spec=CallbackQuery)
        cb.from_user = MagicMock()
        cb.from_user.id = 99
        cb.data = "menu:market"
        user_id, payload = _describe(cb)
        assert user_id == 99
        assert payload == "callback:menu:market"

    def test_unknown_event_type(self) -> None:
        event = MagicMock(spec=TelegramObject)
        user_id, payload = _describe(event)
        assert user_id is None
        assert payload == "MagicMock"


class TestLoggingMiddleware:
    async def test_calls_handler(self) -> None:
        middleware = LoggingMiddleware()
        handler = AsyncMock(return_value="done")
        event = MagicMock(spec=Message)
        event.from_user = MagicMock()
        event.from_user.id = 1
        event.text = "test"
        data: dict = {"key": "value"}

        result = await middleware(handler, event, data)

        assert result == "done"
        handler.assert_awaited_once_with(event, data)

    async def test_re_raises_handler_exception(self) -> None:
        middleware = LoggingMiddleware()
        handler = AsyncMock(side_effect=ValueError("fail"))
        event = MagicMock(spec=Message)
        event.from_user = MagicMock()
        event.from_user.id = 1
        event.text = "test"
        data: dict = {}

        with pytest.raises(ValueError, match="fail"):
            await middleware(handler, event, data)

        handler.assert_awaited_once()
