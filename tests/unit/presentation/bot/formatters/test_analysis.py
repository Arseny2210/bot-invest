"""Unit tests for the analysis formatter."""

from __future__ import annotations

from decimal import Decimal

from moex_analyst.domain.alerts import AlertDirection, AlertSeverity, AlertType
from moex_analyst.presentation.bot.formatters import (
    format_alerts_block,
    format_instrument_analysis,
)
from tests.unit.presentation.bot.formatters.conftest import (
    make_alert,
    make_instrument_analysis,
    make_instrument_dto,
    make_quote_dto,
)


class TestFormatInstrumentAnalysis:
    def test_contains_core_sections(self) -> None:
        text = format_instrument_analysis(make_instrument_analysis())
        for marker in ("<b>", "Trend:", "Support / Resistance", "Indicators", "Outlook"):
            assert marker in text

    def test_includes_shortname_and_ticker_in_title(self) -> None:
        text = format_instrument_analysis(
            make_instrument_analysis(instrument=make_instrument_dto(shortname="Surgut")),
        )
        assert "Surgut" in text
        assert "(SNGS)" in text

    def test_shows_probabilities_as_percent(self) -> None:
        text = format_instrument_analysis(make_instrument_analysis())
        assert "60.0%" in text  # bullish default 0.6

    def test_renders_price_and_daily_change(self) -> None:
        text = format_instrument_analysis(make_instrument_analysis())
        assert "26.40 RUB" in text  # last
        assert "%" in text  # change vs open

    def test_missing_quote_shows_dash(self) -> None:
        text = format_instrument_analysis(make_instrument_analysis(quote=None))
        assert "Last price: —" in text

    def test_missing_instrument_falls_back_to_ticker_title(self) -> None:
        text = format_instrument_analysis(
            make_instrument_analysis(ticker="VTBR", instrument=None, quote=None),
        )
        assert "VTBR" in text

    def test_escapes_dynamic_shortname(self) -> None:
        text = format_instrument_analysis(
            make_instrument_analysis(instrument=make_instrument_dto(shortname="A & <b>B</b>")),
        )
        assert "A &amp; &lt;b&gt;B&lt;/b&gt;" in text

    def test_as_of_footer_present(self) -> None:
        text = format_instrument_analysis(make_instrument_analysis())
        assert "As of 2024-06-01 15:30 UTC" in text

    def test_uses_instrument_decimals_for_price(self) -> None:
        text = format_instrument_analysis(
            make_instrument_analysis(quote=make_quote_dto(last=Decimal("26.4"))),
        )
        assert "26.40 RUB" in text  # 2 decimals from instrument meta


class TestFormatAlertsBlock:
    def test_no_alerts_message(self) -> None:
        assert "No active alerts" in format_alerts_block(())

    def test_lists_each_alert_with_icons(self) -> None:
        alerts = (
            make_alert(severity=AlertSeverity.CRITICAL, direction=AlertDirection.BULLISH,
                       type_=AlertType.STRONG_BULLISH_SIGNAL, message="Strong bullish"),
            make_alert(message="RSI overbought"),
        )
        text = format_alerts_block(alerts)
        assert "Alerts (2)" in text
        assert "Strong bullish" in text
        assert "RSI overbought" in text

    def test_escapes_alert_message(self) -> None:
        text = format_alerts_block((make_alert(message="dip < support & risk"),))
        assert "dip &lt; support &amp; risk" in text
