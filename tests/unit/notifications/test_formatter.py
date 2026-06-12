"""Tests for the notification message formatters."""

from datetime import UTC, datetime

from moex_analyst.application.use_cases.dto import MarketOverview, ScoredInstrument
from moex_analyst.domain.alerts import Alert, AlertDirection, AlertSeverity, AlertType
from moex_analyst.domain.market.timeframe import Timeframe
from moex_analyst.infrastructure.notifications.formatter import (
    format_alert,
    format_alerts,
    format_market_summary,
)
from tests.unit.alerts.conftest import make_result


def _make_alert(
    ticker: str = "SBER",
    timeframe: Timeframe = Timeframe.D1,
    alert_type: AlertType = AlertType.VOLUME_SPIKE,
    direction: AlertDirection = AlertDirection.BULLISH,
    severity: AlertSeverity = AlertSeverity.WARNING,
    score: float = 0.85,
    message: str = "Объём в 3.2x выше среднего",
) -> Alert:
    return Alert(
        type=alert_type,
        direction=direction,
        severity=severity,
        score=score,
        message=message,
        ticker=ticker,
        timeframe=timeframe,
        as_of=datetime(2025, 6, 1, 12, tzinfo=UTC),
    )


def _make_analysis_result(ticker: str = "SBER") -> object:
    return make_result(ticker=ticker, timeframe=Timeframe.D1)


class TestFormatAlert:
    def test_includes_type_ticker_timeframe(self) -> None:
        alert = _make_alert()
        text = format_alert(alert)
        assert "Всплеск объёма" in text
        assert "SBER" in text
        assert "1D" in text

    def test_includes_score(self) -> None:
        alert = _make_alert(score=0.85)
        text = format_alert(alert)
        assert "85%" in text

    def test_includes_message(self) -> None:
        alert = _make_alert(message="Цена пробила поддержку")
        text = format_alert(alert)
        assert "Цена пробила поддержку" in text

    def test_contains_direction_icon(self) -> None:
        alert = _make_alert(direction=AlertDirection.BULLISH)
        text = format_alert(alert)
        assert "🟢" in text

        bearish = _make_alert(direction=AlertDirection.BEARISH)
        assert "🔴" in format_alert(bearish)

    def test_contains_severity_icon(self) -> None:
        alert = _make_alert(severity=AlertSeverity.CRITICAL)
        text = format_alert(alert)
        assert "🚨" in text

    def test_includes_as_of_timestamp(self) -> None:
        alert = _make_alert()
        text = format_alert(alert)
        assert "01.06.2025" in text
        assert "12:00" in text
        assert "UTC" not in text

    def test_html_escapes_dynamic_text(self) -> None:
        alert = _make_alert(ticker="A<B", message="x > y")
        text = format_alert(alert)
        assert "&lt;" in text
        assert "&gt;" in text
        assert "A&lt;B" in text
        assert "x &gt; y" in text


class TestFormatAlerts:
    def test_returns_empty_for_empty_list(self) -> None:
        assert format_alerts([]) == ""

    def test_single_alert_delegates(self) -> None:
        alert = _make_alert()
        result = format_alerts([alert])
        assert result == format_alert(alert)

    def test_same_context_shows_count(self) -> None:
        alerts = [
            _make_alert(message="Оповещение первое"),
            _make_alert(message="Оповещение второе"),
        ]
        text = format_alerts(alerts)
        assert "2 сигнала" in text
        assert "Оповещение первое" in text
        assert "Оповещение второе" in text

    def test_different_context_separated(self) -> None:
        alerts = [
            _make_alert(ticker="SBER", message="Оповещение SBER"),
            _make_alert(ticker="VTBR", message="Оповещение VTBR"),
        ]
        text = format_alerts(alerts)
        assert "SBER" in text
        assert "VTBR" in text


class TestFormatMarketSummary:
    def test_shows_top_instruments(self) -> None:
        overview = MarketOverview(
            timeframe=Timeframe.D1,
            scored=(
                ScoredInstrument(
                    analysis=_make_analysis_result("SBER"),
                    alert_count=2,
                    score=0.85,
                ),
                ScoredInstrument(
                    analysis=_make_analysis_result("VTBR"),
                    alert_count=0,
                    score=0.50,
                ),
            ),
            failed=(),
        )
        text = format_market_summary(overview)
        assert "ЕЖЕДНЕВНАЯ СВОДКА РЫНКА" in text
        assert "SBER" in text
        assert "VTBR" in text
        assert "+0.85" in text

    def test_includes_failed_instruments(self) -> None:
        overview = MarketOverview(
            timeframe=Timeframe.D1,
            scored=(
                ScoredInstrument(
                    analysis=_make_analysis_result("SBER"),
                    alert_count=0,
                    score=0.0,
                ),
            ),
            failed=("GAZP", "ROSN"),
        )
        text = format_market_summary(overview)
        assert "GAZP" in text
        assert "ROSN" in text

    def test_no_scored_instruments(self) -> None:
        overview = MarketOverview(
            timeframe=Timeframe.D1,
            scored=(),
            failed=(),
        )
        text = format_market_summary(overview)
        assert "Нет проанализированных инструментов" in text
