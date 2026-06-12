"""Notification infrastructure — Telegram delivery, deduplication, formatting.

Public surface
--------------
* :class:`InMemoryDeduplicator` — thread-safe in-memory alert deduplication.
* :class:`TelegramNotifier` — ``NotifierPort`` backed by an aiogram ``Bot``.
* :func:`format_alert` — single alert → HTML string.
* :func:`format_alerts` — multiple alerts → HTML string.
* :func:`format_market_summary` — ``MarketOverview`` → HTML string.
"""

from __future__ import annotations

from moex_analyst.infrastructure.notifications.dedup import InMemoryDeduplicator
from moex_analyst.infrastructure.notifications.formatter import (
    format_alert,
    format_alerts,
    format_market_summary,
)
from moex_analyst.infrastructure.notifications.telegram_notifier import (
    TelegramNotifier,
)

__all__ = [
    "InMemoryDeduplicator",
    "TelegramNotifier",
    "format_alert",
    "format_alerts",
    "format_market_summary",
]
