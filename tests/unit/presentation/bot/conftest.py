from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.filters import CommandObject
from aiogram.types import CallbackQuery, Message


@pytest.fixture
def mock_message() -> MagicMock:
    msg = MagicMock(spec=Message)
    msg.from_user = MagicMock()
    msg.from_user.id = 12345
    msg.from_user.first_name = "TestUser"
    msg.text = "/start"
    msg.answer = AsyncMock()
    return msg


@pytest.fixture
def mock_command() -> MagicMock:
    cmd = MagicMock(spec=CommandObject)
    cmd.args = None
    return cmd


@pytest.fixture
def mock_callback() -> MagicMock:
    cb = MagicMock(spec=CallbackQuery)
    cb.from_user = MagicMock()
    cb.from_user.id = 12345
    cb.message = MagicMock(spec=Message)
    cb.message.answer = AsyncMock()
    cb.answer = AsyncMock()
    return cb
