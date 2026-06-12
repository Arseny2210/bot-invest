"""Telegram-backed ``NotifierPort`` implementation.

Delivers alerts via an aiogram ``Bot`` instance.  Every outbound call goes
through an :class:`InMemoryDeduplicator` so the same alert is not sent twice
within the configured TTL.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.enums import ParseMode

from moex_analyst.application.ports.notifier import NotifierPort
from moex_analyst.infrastructure.notifications.formatter import (
    format_alert,
    format_alerts,
    format_market_summary,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from aiogram import Bot

    from moex_analyst.application.use_cases.dto import MarketOverview
    from moex_analyst.domain.alerts import Alert
    from moex_analyst.infrastructure.notifications.dedup import (
        InMemoryDeduplicator,
    )

__all__ = ["TelegramNotifier"]


class TelegramNotifier(NotifierPort):
    """Deliver alerts to a Telegram chat via aiogram Bot."""

    def __init__(
        self,
        bot: Bot,
        deduplicator: InMemoryDeduplicator,
    ) -> None:
        self._bot = bot
        self._dedup = deduplicator

    async def send_alert(self, alert: Alert, chat_id: int) -> None:
        if not self._dedup.check_and_mark(alert):
            return
        text = format_alert(alert)
        await self._bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=ParseMode.HTML,
        )

    async def send_alerts(self, alerts: Sequence[Alert], chat_id: int) -> None:
        unduped = [a for a in alerts if self._dedup.check_and_mark(a)]
        if not unduped:
            return
        text = format_alerts(unduped)
        await self._bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=ParseMode.HTML,
        )

    async def send_market_summary(
        self,
        overview: MarketOverview,
        chat_id: int,
    ) -> None:
        text = format_market_summary(overview)
        await self._bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=ParseMode.HTML,
        )
