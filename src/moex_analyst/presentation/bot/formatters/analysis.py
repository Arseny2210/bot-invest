"""Formatter for the ``/analyze`` command — a full single-instrument report.

Pure: :class:`InstrumentAnalysis` → HTML string. Composes the trend, structure,
support/resistance, indicators, probabilities and alerts into one professional
message body.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from collections.abc import Iterable

    from moex_analyst.application.use_cases.dto import InstrumentAnalysis
    from moex_analyst.domain.alerts import Alert
    from moex_analyst.domain.analysis import AnalysisResult, PriceLevel

__all__ = ["format_alerts_block", "format_instrument_analysis"]

_MAX_LEVELS = 3


def format_instrument_analysis(report: InstrumentAnalysis) -> str:
    """Render a complete analysis report for one instrument."""
    analysis = report.analysis
    title = _title(report)
    decimals = report.instrument.decimals if report.instrument is not None else 2

    lines: list[str] = [
        f"📊 <b>{title}</b>",
        f"<i>{escape(report.timeframe.value)} timeframe · "
        f"{analysis.candles_analysed} candles</i>",
        "",
        _price_line(report, decimals),
        _trend_line(analysis),
        _structure_line(analysis),
        "",
        "<b>Support / Resistance</b>",
        *_levels_lines(analysis, decimals),
        "",
        "<b>Indicators</b>",
        *_indicator_lines(analysis),
        f"• Volume: {volume_label(analysis.volume_condition)}",
        "",
        "<b>Outlook</b>",
        *_probability_lines(analysis),
        "",
        format_alerts_block(report.alerts),
        "",
        f"<i>As of {fmt_datetime(analysis.as_of)}</i>",
    ]
    return "\n".join(lines)


def format_alerts_block(alerts: Iterable[Alert]) -> str:
    """Render the alerts section (or a 'no alerts' note)."""
    materialised = list(alerts)
    if not materialised:
        return "<b>Alerts</b>\n• ✅ No active alerts"
    rows = [
        f"• {alert_severity_icon(a.severity)} {alert_direction_icon(a.direction)} "
        f"{escape(a.message)}"
        for a in materialised
    ]
    return "\n".join([f"<b>Alerts ({len(materialised)})</b>", *rows])


def _title(report: InstrumentAnalysis) -> str:
    ticker = escape(report.ticker)
    if report.instrument is not None and report.instrument.shortname:
        return f"{escape(report.instrument.shortname)} ({ticker})"
    return ticker


def _price_line(report: InstrumentAnalysis, decimals: int) -> str:
    quote = report.quote
    currency = escape(report.instrument.currency) if report.instrument else "RUB"
    if quote is None or quote.last is None:
        return "💰 Last price: —"
    parts = [f"💰 Last price: <b>{fmt_decimal(quote.last, places=decimals)} {currency}</b>"]
    if quote.open is not None and quote.open != 0:
        change = (quote.last - quote.open) / quote.open * 100
        parts.append(f"({float(change):+.2f}% today)")
    return " ".join(parts)


def _trend_line(analysis: AnalysisResult) -> str:
    trend = analysis.trend
    return (
        f"{trend_icon(trend.direction)} Trend: <b>{escape(trend.direction.value)}</b> "
        f"({escape(trend.strength.value)}, score {fmt_score(trend.score)})"
    )


def _structure_line(analysis: AnalysisResult) -> str:
    structure = analysis.structure
    high = structure.last_high.value if structure.last_high is not None else "—"
    low = structure.last_low.value if structure.last_low is not None else "—"
    return f"🏗 Structure: last high <b>{high}</b>, last low <b>{low}</b>"


def _levels_lines(analysis: AnalysisResult, decimals: int) -> list[str]:
    def render(levels: tuple[PriceLevel, ...], label: str, icon: str) -> str:
        if not levels:
            return f"• {icon} {label}: —"
        shown = levels[:_MAX_LEVELS]
        prices = ", ".join(
            f"{fmt_decimal(lvl.price, places=decimals)} "
            f"({fmt_percent(lvl.strength, places=0)})"
            for lvl in shown
        )
        return f"• {icon} {label}: {prices}"

    return [
        render(analysis.resistance_levels, "Resistance", "🔺"),
        render(analysis.support_levels, "Support", "🔻"),
    ]


def _indicator_lines(analysis: AnalysisResult) -> list[str]:
    ind = analysis.indicators
    return [
        f"• RSI(14): {fmt_decimal(ind.rsi14)}",
        f"• EMA(20): {fmt_decimal(ind.ema20)} · EMA(50): {fmt_decimal(ind.ema50)}",
        f"• ATR(14): {fmt_decimal(ind.atr14)}",
    ]


def _probability_lines(analysis: AnalysisResult) -> list[str]:
    probs = analysis.probabilities
    return [
        f"• 🟢 Bullish: {fmt_percent(probs.bullish)}",
        f"• 🔴 Bearish: {fmt_percent(probs.bearish)}",
        f"• ⚪ Sideways: {fmt_percent(probs.sideways)}",
    ]
