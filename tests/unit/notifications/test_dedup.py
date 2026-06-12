"""Tests for the in-memory alert deduplicator."""

from datetime import UTC, datetime

from moex_analyst.domain.alerts import Alert, AlertDirection, AlertSeverity, AlertType
from moex_analyst.domain.market.timeframe import Timeframe
from moex_analyst.infrastructure.notifications.dedup import InMemoryDeduplicator


def _make_alert(
    ticker: str = "SBER",
    timeframe: Timeframe = Timeframe.D1,
    alert_type: AlertType = AlertType.VOLUME_SPIKE,
    direction: AlertDirection = AlertDirection.BULLISH,
) -> Alert:
    return Alert(
        type=alert_type,
        direction=direction,
        severity=AlertSeverity.INFO,
        score=0.5,
        message="Test alert",
        ticker=ticker,
        timeframe=timeframe,
        as_of=datetime(2025, 1, 1, 12, tzinfo=UTC),
    )


class TestInMemoryDeduplicator:
    def test_new_alert_is_not_duplicate(self) -> None:
        dedup = InMemoryDeduplicator(ttl_minutes=60)
        alert = _make_alert()
        assert dedup.check_and_mark(alert) is True

    def test_same_alert_within_ttl_is_duplicate(self) -> None:
        dedup = InMemoryDeduplicator(ttl_minutes=60)
        alert = _make_alert()
        assert dedup.check_and_mark(alert) is True
        assert dedup.check_and_mark(alert) is False

    def test_different_ticker_not_duplicate(self) -> None:
        dedup = InMemoryDeduplicator(ttl_minutes=60)
        a1 = _make_alert(ticker="SBER")
        a2 = _make_alert(ticker="VTBR")
        assert dedup.check_and_mark(a1) is True
        assert dedup.check_and_mark(a2) is True

    def test_different_type_not_duplicate(self) -> None:
        dedup = InMemoryDeduplicator(ttl_minutes=60)
        a1 = _make_alert(alert_type=AlertType.VOLUME_SPIKE)
        a2 = _make_alert(alert_type=AlertType.RSI_OVERSOLD)
        assert dedup.check_and_mark(a1) is True
        assert dedup.check_and_mark(a2) is True

    def test_different_timeframe_not_duplicate(self) -> None:
        dedup = InMemoryDeduplicator(ttl_minutes=60)
        a1 = _make_alert(timeframe=Timeframe.H1)
        a2 = _make_alert(timeframe=Timeframe.H4)
        assert dedup.check_and_mark(a1) is True
        assert dedup.check_and_mark(a2) is True

    def test_after_ttl_expiry_not_duplicate(self) -> None:
        dedup = InMemoryDeduplicator(ttl_minutes=0)  # zero TTL = always fresh
        alert = _make_alert()
        assert dedup.check_and_mark(alert) is True
        assert dedup.check_and_mark(alert) is True

    def test_is_duplicate_without_marking(self) -> None:
        dedup = InMemoryDeduplicator(ttl_minutes=60)
        alert = _make_alert()
        assert dedup.is_duplicate(alert) is False
        dedup.mark_sent(alert)
        assert dedup.is_duplicate(alert) is True

    def test_clear_expired_removes_old_entries(self) -> None:
        dedup = InMemoryDeduplicator(ttl_minutes=60)
        alert = _make_alert()
        dedup.mark_sent(alert)
        cleared = dedup.clear_expired()
        assert cleared == 0  # still within TTL

    def test_dedup_key_based_on_all_fields(self) -> None:
        dedup = InMemoryDeduplicator(ttl_minutes=60)
        alert = _make_alert(
            ticker="SBER", alert_type=AlertType.VOLUME_SPIKE, direction=AlertDirection.BULLISH
        )
        same_key = Alert(
            type=AlertType.VOLUME_SPIKE,
            direction=AlertDirection.BULLISH,
            severity=AlertSeverity.WARNING,
            score=0.9,
            message="Different message",
            ticker="SBER",
            timeframe=Timeframe.D1,
            as_of=datetime(2025, 6, 1, 12, tzinfo=UTC),
        )
        assert dedup.check_and_mark(alert) is True
        assert dedup.check_and_mark(same_key) is False
