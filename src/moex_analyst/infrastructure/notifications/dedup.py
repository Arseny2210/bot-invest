"""In-memory alert deduplication — edge-triggering for notifications.

Tracks which ``{ticker}:{timeframe}:{type}:{direction}`` combinations have
been sent recently so the same alert is not re-delivered within the TTL window.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from moex_analyst.domain.alerts import Alert

__all__ = ["InMemoryDeduplicator"]

_DEFAULT_TTL_MINUTES: int = 60


class InMemoryDeduplicator:
    """Thread-safe deduplication keyed on ``Alert.dedup_key``.

    Usage::

        dedup = InMemoryDeduplicator(ttl_minutes=60)
        if dedup.check_and_mark(alert):
            ...  # send the alert
    """

    def __init__(self, ttl_minutes: int = _DEFAULT_TTL_MINUTES) -> None:
        self._sent: dict[str, datetime] = {}
        self._ttl = timedelta(minutes=ttl_minutes)
        self._lock = Lock()

    def check_and_mark(self, alert: Alert) -> bool:
        """Atomically check if *alert* is a duplicate and mark it as sent.

        Returns ``True`` when the alert should be delivered (not a duplicate),
        ``False`` when it was already sent within the TTL window.
        """
        key = alert.dedup_key
        with self._lock:
            last_sent = self._sent.get(key)
            now = datetime.now(UTC)
            if last_sent is not None and now - last_sent < self._ttl:
                return False
            self._sent[key] = now
            return True

    def is_duplicate(self, alert: Alert) -> bool:
        """Check whether *alert* was sent recently, without marking it."""
        key = alert.dedup_key
        with self._lock:
            last_sent = self._sent.get(key)
            if last_sent is None:
                return False
            return datetime.now(UTC) - last_sent < self._ttl

    def mark_sent(self, alert: Alert) -> None:
        """Record *alert* as having been sent (idempotent)."""
        with self._lock:
            self._sent[alert.dedup_key] = datetime.now(UTC)

    def clear_expired(self) -> int:
        """Remove entries older than TTL; returns how many were purged."""
        cutoff = datetime.now(UTC) - self._ttl
        with self._lock:
            before = len(self._sent)
            self._sent = {k: v for k, v in self._sent.items() if v >= cutoff}
            return before - len(self._sent)
