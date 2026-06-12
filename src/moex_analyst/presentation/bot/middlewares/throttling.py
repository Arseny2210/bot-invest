"""In-memory per-user throttling.

A lightweight sliding-window limiter: each user may trigger at most
``limit_per_minute`` updates within any 60-second window. Excess updates are
dropped with a short notice rather than reaching the handlers. State is
process-local (no Redis dependency) — adequate for single-process polling.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

__all__ = ["ThrottlingMiddleware"]

_WINDOW_SECONDS = 60.0


class ThrottlingMiddleware(BaseMiddleware):
    """Drops updates that exceed a per-user per-minute budget."""

    def __init__(self, limit_per_minute: int) -> None:
        self._limit = limit_per_minute
        self._hits: dict[int, deque[float]] = defaultdict(deque)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_id = _user_id(event)
        if user_id is not None and self._is_throttled(user_id):
            await _notify(event)
            return None
        return await handler(event, data)

    def _is_throttled(self, user_id: int) -> bool:
        now = time.monotonic()
        hits = self._hits[user_id]
        cutoff = now - _WINDOW_SECONDS
        while hits and hits[0] < cutoff:
            hits.popleft()
        if len(hits) >= self._limit:
            return True
        hits.append(now)
        return False


def _user_id(event: TelegramObject) -> int | None:
    if isinstance(event, Message | CallbackQuery) and event.from_user is not None:
        return event.from_user.id
    return None


async def _notify(event: TelegramObject) -> None:
    notice = "⏳ Слишком много запросов — пожалуйста, немного замедлитесь."
    if isinstance(event, CallbackQuery):
        await event.answer(notice, show_alert=False)
    elif isinstance(event, Message):
        await event.answer(notice)
