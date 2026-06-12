"""Alert message formatters — pure functions that produce Telegram HTML strings."""

from __future__ import annotations

from html import escape as _html_escape
from typing import TYPE_CHECKING

from moex_analyst.domain.alerts.enums import AlertDirection, AlertSeverity, AlertType
from moex_analyst.infrastructure.moex.config import INSTRUMENT_REGISTRY

if TYPE_CHECKING:
    from collections.abc import Sequence

    from moex_analyst.application.use_cases.dto import MarketOverview
    from moex_analyst.domain.alerts import Alert

__all__ = [
    "format_alert",
    "format_alerts",
    "format_market_summary",
]

_SECTION_DIVIDER = "━" * 24

_DIRECTION_ICONS: dict[AlertDirection, str] = {
    AlertDirection.BULLISH: "🟢",
    AlertDirection.BEARISH: "🔴",
    AlertDirection.NEUTRAL: "⚪",
}

_DIRECTION_LABELS: dict[AlertDirection, str] = {
    AlertDirection.BULLISH: "Бычий",
    AlertDirection.BEARISH: "Медвежий",
    AlertDirection.NEUTRAL: "Нейтральный",
}

_SEVERITY_LABELS: dict[AlertSeverity, str] = {
    AlertSeverity.INFO: "ℹ️ Информация",
    AlertSeverity.WARNING: "⚠️ Важный",
    AlertSeverity.CRITICAL: "🚨 Критический",
}

_ALERT_TYPE_LABELS: dict[AlertType, str] = {
    AlertType.SUPPORT_BREAKDOWN: "Пробой поддержки",
    AlertType.RESISTANCE_BREAKOUT: "Пробой сопротивления",
    AlertType.TREND_CHANGE: "Смена тренда",
    AlertType.EMA20_CROSS_EMA50: "Пересечение EMA20/EMA50",
    AlertType.RSI_OVERBOUGHT: "RSI перекуплен",
    AlertType.RSI_OVERSOLD: "RSI перепродан",
    AlertType.VOLUME_SPIKE: "Всплеск объёма",
    AlertType.MARKET_STRUCTURE_CHANGE: "Смена структуры рынка",
    AlertType.STRONG_BULLISH_SIGNAL: "Сильный бычий сигнал",
    AlertType.STRONG_BEARISH_SIGNAL: "Сильный медвежий сигнал",
}


def _esc(text: str) -> str:
    return _html_escape(text, quote=False)


def _fmt_ticker(ticker: str) -> str:
    """Return ``Name (TICKER)`` for a tracked instrument or bare ticker."""
    ref = INSTRUMENT_REGISTRY.get(ticker)
    if ref is None or not ref.display_name_ru:
        return _esc(ticker)
    return f"{_esc(ref.display_name_ru)} ({_esc(ref.ticker)})"


def format_alert(alert: Alert) -> str:
    """Render a single :class:`Alert` as a professional Telegram HTML message."""
    sev = _SEVERITY_LABELS.get(alert.severity, alert.severity.value)
    sev_icon = _DIRECTION_ICONS.get(alert.direction, "⚪")
    dir_label = _DIRECTION_LABELS.get(alert.direction, alert.direction.value)
    type_label = _ALERT_TYPE_LABELS.get(alert.type, alert.type.value)
    t = _fmt_ticker(alert.ticker)
    tf = _esc(alert.timeframe.value)
    msg = _esc(alert.message)
    as_of = alert.as_of.strftime("%d.%m.%Y %H:%M")
    score_pct = f"{alert.score * 100:.0f}%"

    return (
        f"{_SECTION_DIVIDER}\n"
        f"🚨 <b>НОВЫЙ СИГНАЛ</b>\n"
        f"{_SECTION_DIVIDER}\n"
        f"\n"
        f"📌 Инструмент:        {t}\n"
        f"📋 Тип:               {_esc(type_label)}\n"
        f"🎯 Направление:       {sev_icon} {dir_label}\n"
        f"⚠️ Важность:          {sev}\n"
        f"📊 Вероятность:       {score_pct}\n"
        f"⏰ Таймфрейм:         {tf}\n"
        f"\n"
        f"<b>Причина:</b>\n"
        f"{msg}\n"
        f"\n"
        f"📅 {as_of}\n"
        f"{_SECTION_DIVIDER}"
    )


def format_alerts(alerts: Sequence[Alert]) -> str:
    """Render multiple alerts into one Telegram HTML message."""
    if not alerts:
        return ""

    if len(alerts) == 1:
        return format_alert(alerts[0])

    first = alerts[0]
    same_context = all(a.ticker == first.ticker and a.timeframe == first.timeframe for a in alerts)

    if same_context:
        t = _fmt_ticker(first.ticker)
        tf = _esc(first.timeframe.value)
        lines: list[str] = [
            _SECTION_DIVIDER,
            f"🚨 <b>{t} @ {tf}</b> — {len(alerts)} сигнала",
            _SECTION_DIVIDER,
            "",
        ]
        for a in alerts:
            sev = _SEVERITY_LABELS.get(a.severity, a.severity.value)
            dir_icon = _DIRECTION_ICONS.get(a.direction, "⚪")
            dir_label = _DIRECTION_LABELS.get(a.direction, a.direction.value)
            type_label = _ALERT_TYPE_LABELS.get(a.type, a.type.value)
            msg = _esc(a.message)
            lines.append(f"{sev} {dir_icon} <b>{_esc(type_label)}</b>")
            lines.append(f"   {dir_label} — {msg}")
            lines.append("")
        lines.append(_SECTION_DIVIDER)
        return "\n".join(lines)

    return "\n\n".join(format_alert(a) for a in alerts)


def format_market_summary(overview: MarketOverview) -> str:
    """Render a :class:`MarketOverview` as a Telegram HTML message."""
    tf = _esc(overview.timeframe.value)
    lines: list[str] = [
        _SECTION_DIVIDER,
        f"📈 <b>ЕЖЕДНЕВНАЯ СВОДКА РЫНКА</b> — {tf}",
        _SECTION_DIVIDER,
        "",
    ]

    if overview.scored:
        bullish = sum(1 for s in overview.scored if s.score >= 0.1)
        bearish = sum(1 for s in overview.scored if s.score <= -0.1)
        lines.append(f"📊 <b>Всего: {len(overview.scored)} инструментов</b>")
        lines.append(f"   🟢 Бычьих:     {bullish}")
        lines.append(f"   🔴 Медвежьих:  {bearish}")
        lines.append("")
        lines.append("<b>Детально:</b>")
        for s in overview.scored:
            t = _fmt_ticker(s.analysis.ticker)
            alert_note = f" ⚡{s.alert_count}" if s.alert_count else ""
            lines.append(
                f"   • {t} — оценка <b>{s.score:+.2f}</b>{alert_note}",
            )
    else:
        lines.append("<b>Нет проанализированных инструментов</b>")

    if overview.failed:
        failed_str = ", ".join(_esc(t) for t in overview.failed)
        lines.extend(["", f"⚠️ Ошибка: {failed_str}"])

    if overview.scored:
        as_of = overview.scored[0].analysis.as_of
        lines.extend(
            [
                "",
                f"📅 {as_of.strftime('%d.%m.%Y %H:%M')}",
                _SECTION_DIVIDER,
            ]
        )
    return "\n".join(lines)
