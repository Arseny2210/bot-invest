"""Structured request logging for every incoming update.

Binds the user id and a short description of the update (command text or
callback data) into the Loguru context, so handler logs are attributable.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from loguru import logger

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

__all__ = ["LoggingMiddleware"]


class LoggingMiddleware(BaseMiddleware):
    """Logs each handled update with the originating user and payload."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_id, payload = _describe(event)
        bound = logger.bind(service="bot", user_id=user_id)
        bound.info("update received: {}", payload)
        try:
            return await handler(event, data)
        except Exception:
            bound.exception("handler raised on update: {}", payload)
            raise


def _describe(event: TelegramObject) -> tuple[int | None, str]:
    if isinstance(event, Message):
        return (event.from_user.id if event.from_user else None, event.text or "<non-text>")
    if isinstance(event, CallbackQuery):
        return (event.from_user.id, f"callback:{event.data}")
    return (None, type(event).__name__)
