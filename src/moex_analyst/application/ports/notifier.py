"""Notifier port — the outbound alert delivery abstraction.

This interface lives in the application layer and is intentionally free of any
Telegram / e-mail / SMS detail. Use cases depend on this abstraction; concrete
implementations live in :mod:`moex_analyst.infrastructure.notifications`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from moex_analyst.application.use_cases.dto import MarketOverview
    from moex_analyst.domain.alerts import Alert

__all__ = ["NotifierPort"]


class NotifierPort(ABC):
    """Outbound port for delivering alerts to a human (Telegram chat, etc.)."""

    @abstractmethod
    async def send_alert(self, alert: Alert, chat_id: int) -> None:
        """Deliver a single alert."""

    @abstractmethod
    async def send_alerts(self, alerts: Sequence[Alert], chat_id: int) -> None:
        """Deliver a batch of alerts (deduplication is implementation-specific)."""

    @abstractmethod
    async def send_market_summary(
        self,
        overview: MarketOverview,
        chat_id: int,
    ) -> None:
        """Deliver a daily/weekly market summary."""
