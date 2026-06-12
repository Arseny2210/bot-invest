"""Shared helpers for bot handlers.

Centralises the "update in place, never clutter the chat" message policy so
every screen — analysis refresh, market/signals refresh, menu navigation —
behaves identically: one message per dialog, edited on every update.
"""

from __future__ import annotations

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, Message
from loguru import logger

__all__ = ["edit_or_answer"]


async def edit_or_answer(
    message: Message,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    """Update ``message`` in place; only send a new message on a real failure.

    Telegram raises :class:`TelegramBadRequest` both when the new content is
    identical to what is already shown ("message is not modified") and when the
    message genuinely cannot be edited (too old, deleted, …). The former is a
    no-op success — re-sending would clutter the chat with a duplicate — so it
    is swallowed. Any other failure falls back to a fresh message and is logged
    with the reason.
    """
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc).lower():
            return
        logger.warning("edit_text failed (not sending a new message): {}", exc)
