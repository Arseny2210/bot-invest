"""Unit tests for the low-level text helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from decimal import Decimal

from moex_analyst.domain.alerts.enums import AlertDirection, AlertSeverity
from moex_analyst.domain.analysis.enums import TrendDirection, VolumeCondition
from moex_analyst.domain.market.timeframe import Timeframe
from moex_analyst.presentation.bot.formatters.text import (
    alert_direction_icon,
    alert_severity_icon,
    escape,
    fmt_datetime,
    fmt_datetime_msk,
    fmt_decimal,
    fmt_freshness_block,
    fmt_percent,
    fmt_score,
    is_stale,
    trend_icon,
    volume_label,
)


class TestEscape:
    def test_escapes_html_special_chars(self) -> None:
        assert escape("A & B <tag>") == "A &amp; B &lt;tag&gt;"

    def test_plain_text_unchanged(self) -> None:
        assert escape("SNGS") == "SNGS"


class TestFmtDecimal:
    def test_none_is_em_dash(self) -> None:
        assert fmt_decimal(None) == "—"

    def test_quantizes_to_places(self) -> None:
        assert fmt_decimal(Decimal("26.1"), places=2) == "26.10"

    def test_thousands_separator(self) -> None:
        assert fmt_decimal(Decimal("1234.5"), places=2) == "1,234.50"


class TestFmtPercentAndScore:
    def test_percent(self) -> None:
        assert fmt_percent(0.5) == "50.0%"
        assert fmt_percent(0.123, places=0) == "12%"

    def test_score_is_signed(self) -> None:
        assert fmt_score(0.7) == "+0.70"
        assert fmt_score(-0.3) == "-0.30"


class TestFmtDatetime:
    def test_utc_format(self) -> None:
        value = datetime(2024, 6, 1, 15, 30, tzinfo=UTC)
        assert fmt_datetime(value) == "01.06.2024 15:30"


class TestFmtDatetimeMsk:
    def test_converts_utc_to_msk_and_labels(self) -> None:
        # 12:42 UTC -> 15:42 MSK (UTC+3)
        value = datetime(2026, 6, 2, 12, 42, tzinfo=UTC)
        assert fmt_datetime_msk(value) == "02.06.2026 15:42 МСК"

    def test_naive_assumed_utc(self) -> None:
        value = datetime(2026, 6, 2, 12, 42)  # noqa: DTZ001 - intentional naive input
        assert fmt_datetime_msk(value) == "02.06.2026 15:42 МСК"

    def test_day_rollover_across_midnight(self) -> None:
        # 22:30 UTC -> 01:30 MSK next day
        value = datetime(2026, 6, 2, 22, 30, tzinfo=UTC)
        assert fmt_datetime_msk(value) == "03.06.2026 01:30 МСК"


class TestFreshnessBlock:
    def test_fresh_block_contents(self) -> None:
        fresh = datetime.now(UTC)
        block = fmt_freshness_block(fresh, Timeframe.D1)
        assert "🕒 Последнее обновление:" in block
        assert "📡 Источник: MOEX ISS" in block
        assert "🟢 Актуальные данные" in block
        assert "МСК" in block
        # No stale warning when fresh.
        assert "⚠️" not in block

    def test_stale_block_shows_warning_and_refresh_indicator(self) -> None:
        old = datetime.now(UTC) - timedelta(days=3)
        block = fmt_freshness_block(old, Timeframe.D1)  # D1 threshold = 1 day
        assert "🟡 Требуется обновление" in block
        assert "⚠️ Данные могли устареть." in block
        assert "🟢 Актуальные данные" not in block

    def test_is_stale_thresholds(self) -> None:
        now = datetime.now(UTC)
        assert is_stale(now - timedelta(minutes=25), Timeframe.M15) is True
        assert is_stale(now - timedelta(minutes=10), Timeframe.M15) is False
        assert is_stale(now - timedelta(hours=2), Timeframe.H1) is True
        assert is_stale(now - timedelta(hours=6), Timeframe.H4) is True
        assert is_stale(now - timedelta(days=8), Timeframe.W1) is True
        assert is_stale(now - timedelta(days=2), Timeframe.W1) is False


class TestIcons:
    def test_trend_icons_cover_all_directions(self) -> None:
        for direction in TrendDirection:
            assert trend_icon(direction)

    def test_alert_direction_icons_cover_all(self) -> None:
        for direction in AlertDirection:
            assert alert_direction_icon(direction)

    def test_alert_severity_icons_cover_all(self) -> None:
        for severity in AlertSeverity:
            assert alert_severity_icon(severity)

    def test_volume_labels_cover_all(self) -> None:
        for condition in VolumeCondition:
            assert volume_label(condition)
