"""Unit tests for the analysis formatter."""

from __future__ import annotations

from decimal import Decimal

from loguru import logger

from moex_analyst.domain.alerts import AlertDirection, AlertSeverity, AlertType
from moex_analyst.presentation.bot.formatters import (
    format_alerts_block,
    format_instrument_analysis,
)
from moex_analyst.presentation.bot.formatters.analysis import MAX_TELEGRAM_LEN
from moex_analyst.presentation.bot.formatters.text import fmt_instrument_name
from tests.unit.presentation.bot.formatters.conftest import (
    make_alert,
    make_analysis_result,
    make_instrument_analysis,
    make_instrument_dto,
    make_quote_dto,
)


class TestFormatInstrumentAnalysis:
    def test_contains_core_sections(self) -> None:
        text = format_instrument_analysis(make_instrument_analysis())
        for marker in ("<b>", "ТРЕНД", "УРОВНИ", "ИНДИКАТОРЫ", "ПРОГНОЗ"):
            assert marker in text

    def test_contains_new_sections(self) -> None:
        text = format_instrument_analysis(make_instrument_analysis())
        for marker in (
            "СЦЕНАРИЙ",
            "РИСК/ПРИБЫЛЬ",
            "НАДЁЖНОСТЬ СИГНАЛА",
            "ПРОГНОЗ ПО ГОРИЗОНТАМ",
            "КРАТКИЙ ВЫВОД",
            "ПОЧЕМУ ТАКОЙ ПРОГНОЗ",
        ):
            assert marker in text

    def test_uses_new_wording_not_legacy(self) -> None:
        text = format_instrument_analysis(make_instrument_analysis())
        assert "Инвалидация" not in text
        assert "УВЕРЕННОСТЬ" not in text
        assert "Отмена сценария" in text

    def test_marks_dominant_scenario_as_active(self) -> None:
        # Default fixture is bullish-dominant (0.6 vs 0.25).
        text = format_instrument_analysis(make_instrument_analysis())
        assert "основной" in text

    def test_indicator_descriptions_present(self) -> None:
        # RSI default 72 → overbought note.
        text = format_instrument_analysis(make_instrument_analysis())
        assert "перекупленность" in text

    def test_fits_single_telegram_message(self) -> None:
        text = format_instrument_analysis(make_instrument_analysis())
        assert len(text) <= MAX_TELEGRAM_LEN

    def test_includes_instrument_name_and_ticker_in_title(self) -> None:
        text = format_instrument_analysis(
            make_instrument_analysis(instrument=make_instrument_dto(shortname="Surgut")),
        )
        assert fmt_instrument_name("SNGS") in text
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
        assert "Цена:" in text
        assert "—" in text

    def test_missing_instrument_falls_back_to_ticker_title(self) -> None:
        text = format_instrument_analysis(
            make_instrument_analysis(ticker="VTBR", instrument=None, quote=None),
        )
        assert "VTBR" in text

    def test_escapes_dynamic_conclusion(self) -> None:
        text = format_instrument_analysis(make_instrument_analysis(instrument=None))
        assert "КРАТКИЙ ВЫВОД" in text

    def test_as_of_footer_present(self) -> None:
        text = format_instrument_analysis(make_instrument_analysis())
        # Spec footer: МСК timestamp (15:30 UTC -> 18:30 MSK) + data source.
        assert "Последнее обновление:" in text
        assert "01.06.2024 18:30 МСК" in text
        assert "Источник: MOEX ISS" in text

    def test_uses_instrument_decimals_for_price(self) -> None:
        text = format_instrument_analysis(
            make_instrument_analysis(quote=make_quote_dto(last=Decimal("26.4"))),
        )
        assert "26.40 RUB" in text  # 2 decimals from instrument meta

    def test_no_quote_still_renders_new_sections(self) -> None:
        text = format_instrument_analysis(make_instrument_analysis(quote=None))
        assert "СЦЕНАРИЙ" in text
        assert "КРАТКИЙ ВЫВОД" in text
        # No price → no setup → Risk/Reward hidden, scenario shows the info note.
        assert "РИСК/ПРИБЫЛЬ" not in text
        assert "нет качественной точки входа" in text

    def test_oversized_report_trims_to_single_message(self) -> None:
        # A flood of long alerts pushes the full render past the Telegram limit;
        # alerts are the first block dropped, so the result must still fit.
        alerts = tuple(make_alert(message="оповещение " + "x" * 200) for _ in range(60))
        report = make_instrument_analysis(alerts=alerts)
        text = format_instrument_analysis(report)
        assert len(text) <= MAX_TELEGRAM_LEN
        assert "Сообщение сокращено" in text
        # Never-trim content survives.
        assert "СЦЕНАРИЙ" in text
        assert "КРАТКИЙ ВЫВОД" in text
        assert "ВЕРОЯТНОСТИ" in text


class TestScenarioAvailability:
    def _no_levels_report(self):  # type: ignore[no-untyped-def]
        return make_instrument_analysis(analysis=make_analysis_result(with_levels=False))

    def test_no_setup_shows_info_not_error(self) -> None:
        text = format_instrument_analysis(self._no_levels_report())
        assert "нет качественной точки входа" in text
        assert "цена находится между ключевыми уровнями" in text
        # The harsh legacy placeholders must never appear.
        assert "Недостаточно данных для сценария" not in text
        assert "Недостаточно данных" not in text

    def test_risk_reward_hidden_when_no_setup(self) -> None:
        text = format_instrument_analysis(self._no_levels_report())
        assert "РИСК/ПРИБЫЛЬ" not in text

    def test_risk_reward_shown_when_setup_exists(self) -> None:
        text = format_instrument_analysis(make_instrument_analysis())
        assert "РИСК/ПРИБЫЛЬ" in text

    def test_fallback_scenario_renders_when_price_above_levels(self) -> None:
        # Quote above both levels: no breakout overhead, but the uptrend builds
        # a fallback continuation, so a real scenario (not the info note) shows.
        report = make_instrument_analysis(quote=make_quote_dto(last=Decimal("40.00")))
        text = format_instrument_analysis(report)
        assert "БЫЧИЙ" in text
        assert "нет качественной точки входа" not in text
        assert "РИСК/ПРИБЫЛЬ" in text

    def test_skip_reason_is_logged(self) -> None:
        records: list[str] = []
        handle = logger.add(records.append, level="INFO")
        try:
            format_instrument_analysis(self._no_levels_report())
        finally:
            logger.remove(handle)
        assert any("scenario_generation_skipped" in r and "missing_levels" in r for r in records)


class TestFormatAlertsBlock:
    def test_no_alerts_message(self) -> None:
        assert "Нет активных оповещений" in format_alerts_block(())

    def test_lists_each_alert_with_icons(self) -> None:
        alerts = (
            make_alert(
                severity=AlertSeverity.CRITICAL,
                direction=AlertDirection.BULLISH,
                type_=AlertType.STRONG_BULLISH_SIGNAL,
                message="Сильный бычий сигнал",
            ),
            make_alert(message="RSI перекуплен"),
        )
        text = format_alerts_block(alerts)
        assert "ОПОВЕЩЕНИЯ (2)" in text
        assert "Сильный бычий сигнал" in text
        assert "RSI перекуплен" in text

    def test_escapes_alert_message(self) -> None:
        text = format_alerts_block((make_alert(message="пробой поддержки & риск"),))
        assert "пробой поддержки &amp; риск" in text
