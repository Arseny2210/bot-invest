"""Unit tests for the low-level text helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from moex_analyst.domain.alerts.enums import AlertDirection, AlertSeverity
from moex_analyst.domain.analysis.enums import TrendDirection, VolumeCondition
from moex_analyst.presentation.bot.formatters.text import (
    alert_direction_icon,
    alert_severity_icon,
    escape,
    fmt_datetime,
    fmt_decimal,
    fmt_percent,
    fmt_score,
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
        assert fmt_datetime(value) == "2024-06-01 15:30 UTC"


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
