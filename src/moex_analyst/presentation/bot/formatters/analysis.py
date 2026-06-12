from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from moex_analyst.domain.analysis.scenarios import (
    COMPONENT_WEIGHTS,
    build_scenarios,
    compute_conclusion,
    compute_confidence_breakdown,
    compute_horizons,
    compute_indicator_notes,
    compute_reasoning,
    compute_risk_reward,
)
from moex_analyst.presentation.bot.formatters.text import (
    alert_direction_icon,
    alert_severity_icon,
    escape,
    fmt_decimal,
    fmt_freshness_block,
    fmt_instrument_name,
    fmt_percent,
    fmt_score,
    section_divider,
    structure_point_label,
    trend_direction_label,
    trend_icon,
    trend_strength_label,
    volume_label,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from decimal import Decimal

    from moex_analyst.application.use_cases.dto import InstrumentAnalysis
    from moex_analyst.domain.alerts import Alert
    from moex_analyst.domain.analysis import AnalysisResult, PriceLevel
    from moex_analyst.domain.analysis.scenarios import ScenarioOutcome

__all__ = ["format_alerts_block", "format_instrument_analysis"]

_MAX_LEVELS = 3

# Telegram caps a single text message at 4096 characters. The analysis report
# is always delivered as one message, so when the fully detailed render exceeds
# this budget we drop optional blocks in a fixed priority order (see
# ``format_instrument_analysis``) rather than splitting across messages.
MAX_TELEGRAM_LEN = 4096
_TRIM_NOTICE = "✂️ <i>Сообщение сокращено, чтобы уместиться в одно.</i>"


def format_instrument_analysis(report: InstrumentAnalysis) -> str:
    """Render the full analysis as a single Telegram message (≤ 4096 chars).

    The report is built at decreasing levels of detail and the first render
    that fits the Telegram limit is returned. Blocks are dropped in this order
    (most expendable first): alerts → the "why" block → detailed explanations
    (indicator notes and the reliability breakdown). Price, trend,
    probabilities, scenarios and the summary are never dropped.

    Scenario generation runs once up front; any skipped sides are logged with
    their reason code (never shown to the user).
    """
    analysis = report.analysis
    decimals = report.instrument.decimals if report.instrument is not None else 2
    price = report.quote.last if report.quote is not None else None
    scenarios = build_scenarios(analysis, price, decimals)
    for reason in scenarios.skip_reasons:
        logger.info("scenario_generation_skipped: {}", reason)

    # (include_alerts, include_why, include_details)
    for include_alerts, include_why, include_details in (
        (True, True, True),
        (False, True, True),
        (False, False, True),
        (False, False, False),
    ):
        trimmed = not (include_alerts and include_why and include_details)
        text = _render(
            report,
            scenarios,
            include_alerts=include_alerts,
            include_why=include_why,
            include_details=include_details,
            trimmed=trimmed,
        )
        if len(text) <= MAX_TELEGRAM_LEN:
            return text

    # Pathological fallback: even the leanest render is too long. Hard-trim.
    return text[: MAX_TELEGRAM_LEN - len(_TRIM_NOTICE) - 1] + "\n" + _TRIM_NOTICE


def _render(
    report: InstrumentAnalysis,
    scenarios: ScenarioOutcome,
    *,
    include_alerts: bool,
    include_why: bool,
    include_details: bool,
    trimmed: bool,
) -> str:
    analysis = report.analysis
    ticker_label = fmt_instrument_name(report.ticker)
    decimals = report.instrument.decimals if report.instrument is not None else 2
    price = report.quote.last if report.quote is not None else None
    tf = escape(report.timeframe.value)

    # Risk/Reward is only meaningful when a trade setup exists, so the whole
    # section is hidden otherwise (rather than showing a "no data" placeholder).
    risk_reward_section: list[str] = []
    if scenarios.has_setup:
        risk_reward_section = [
            section_divider(),
            "⚖️ <b>РИСК/ПРИБЫЛЬ</b>",
            section_divider(),
            "",
            *_risk_reward_lines(analysis, price, decimals),
            "",
        ]

    lines: list[str] = [
        section_divider(),
        "📈 <b>Анализ</b>",
        ticker_label,
        section_divider(),
        "",
        _price_line(report, decimals),
        f"⏰ Таймфрейм:          {tf} · {analysis.candles_analysed} свечей",
        fmt_freshness_block(analysis.as_of, analysis.timeframe),
        "",
        section_divider(),
        "📊 <b>ТРЕНД</b>",
        section_divider(),
        "",
        _trend_block(analysis),
        "",
        section_divider(),
        "📉 <b>УРОВНИ</b>",
        section_divider(),
        "",
        *_levels_lines(analysis, price, decimals),
        "",
        section_divider(),
        "📐 <b>ИНДИКАТОРЫ</b>",
        section_divider(),
        "",
        *_indicator_lines(analysis, price, detailed=include_details),
        f"📊 Объём:              {volume_label(analysis.volume_condition)}",
        "",
        section_divider(),
        "🎯 <b>ВЕРОЯТНОСТИ</b>",
        section_divider(),
        "",
        *_probability_lines(analysis),
        "",
        section_divider(),
        "📌 <b>СЦЕНАРИЙ</b>",
        section_divider(),
        "",
        *_scenario_lines(analysis, scenarios),
        "",
        *risk_reward_section,
        section_divider(),
        _confidence_header(analysis),
        section_divider(),
        "",
        *_confidence_lines(analysis, detailed=include_details),
        "",
        section_divider(),
        "🔮 <b>ПРОГНОЗ ПО ГОРИЗОНТАМ</b>",
        section_divider(),
        "",
        *_horizons_lines(analysis),
        "",
        section_divider(),
        "💡 <b>КРАТКИЙ ВЫВОД</b>",
        section_divider(),
        "",
        _conclusion_line(analysis, price),
        "",
    ]

    if include_why:
        lines += [
            section_divider(),
            "❓ <b>ПОЧЕМУ ТАКОЙ ПРОГНОЗ</b>",
            section_divider(),
            "",
            *_why_lines(analysis, price),
            "",
        ]

    if include_alerts:
        lines += [
            section_divider(),
            format_alerts_block(report.alerts),
            section_divider(),
        ]

    if trimmed:
        lines += ["", _TRIM_NOTICE]

    return "\n".join(lines)


def format_alerts_block(alerts: Iterable[Alert]) -> str:
    materialised = list(alerts)
    if not materialised:
        return "✅ Нет активных оповещений\n"
    rows: list[str] = []
    for a in materialised:
        rows.append(
            f"• {alert_severity_icon(a.severity)} {alert_direction_icon(a.direction)} "
            f"{escape(a.message)}"
        )
    header = f"🚨 <b>ОПОВЕЩЕНИЯ ({len(materialised)})</b>"
    return "\n".join([header, *rows, ""])


def _price_line(report: InstrumentAnalysis, decimals: int) -> str:
    quote = report.quote
    currency = escape(report.instrument.currency) if report.instrument else "RUB"
    if quote is None or quote.last is None:
        return "💰 <b>Цена:</b>               —"
    change_str = ""
    if quote.open is not None and quote.open != 0:
        change = (quote.last - quote.open) / quote.open * 100
        change_str = f" ({float(change):+.2f}%)"
    return (
        f"💰 <b>Цена:</b>               "
        f"{fmt_decimal(quote.last, places=decimals)} {currency}{change_str}"
    )


def _trend_block(analysis: AnalysisResult) -> str:
    trend = analysis.trend
    direction = trend_direction_label(trend.direction)
    strength = trend_strength_label(trend.strength)
    structure = analysis.structure
    high = structure_point_label(structure.last_high) if structure.last_high is not None else "—"
    low = structure_point_label(structure.last_low) if structure.last_low is not None else "—"
    return (
        f"{trend_icon(trend.direction)} Направление:      <b>{direction}</b>\n"
        f"📊 Сила:               <b>{strength}</b>\n"
        f"📉 Оценка:             {fmt_score(trend.score)}\n"
        f"🏗 Структура:          {high} → {low}"
    )


def _levels_lines(
    analysis: AnalysisResult,
    price: Decimal | None,
    decimals: int,
) -> list[str]:
    def render_one(
        levels: tuple[PriceLevel, ...],
        label: str,
        icon: str,
        *,
        ascending: bool,
    ) -> str:
        if not levels:
            return f"{icon} {label}:       —"
        # Sort by price proximity to the current quote: resistances ascending
        # (nearest above first), supports descending (nearest below first).
        ordered = sorted(levels, key=lambda lvl: lvl.price, reverse=not ascending)
        shown = ordered[:_MAX_LEVELS]
        parts = []
        for lvl in shown:
            reliability = int(lvl.strength * 100)
            parts.append(f"{fmt_decimal(lvl.price, places=decimals)} ₽ (надёжность {reliability}%)")
        return f"{icon} {label}:  " + ", ".join(parts)

    return [
        render_one(analysis.resistance_levels, "Сопротивление", "🔺", ascending=True),
        render_one(analysis.support_levels, "Поддержка", "🔻", ascending=False),
    ]


def _indicator_lines(
    analysis: AnalysisResult,
    price: Decimal | None,
    *,
    detailed: bool,
) -> list[str]:
    ind = analysis.indicators
    notes = compute_indicator_notes(analysis, price) if detailed else {}

    def line(label_block: str, key: str) -> str:
        note = notes.get(key)
        return f"{label_block} · {note}" if note else label_block

    return [
        line(f"📈 RSI(14):            {fmt_decimal(ind.rsi14)}", "rsi"),
        line(f"📈 EMA(20):            {fmt_decimal(ind.ema20)}", "ema20"),
        line(f"📈 EMA(50):            {fmt_decimal(ind.ema50)}", "ema50"),
        line(f"📈 ATR(14):            {fmt_decimal(ind.atr14)}", "atr14"),
    ]


def _probability_lines(analysis: AnalysisResult) -> list[str]:
    probs = analysis.probabilities
    return [
        f"🟢 Рост:              {fmt_percent(probs.bullish)}",
        f"🔴 Падение:           {fmt_percent(probs.bearish)}",
        f"🟡 Боковик:           {fmt_percent(probs.sideways)}",
    ]


_NO_SETUP_LINES = [
    "ℹ️ Сейчас нет качественной точки входа.",
    "",
    "Причина:",
    "• цена находится между ключевыми уровнями",
    "• или отсутствует подтверждение сценария",
]


def _scenario_lines(
    analysis: AnalysisResult,
    scenarios: ScenarioOutcome,
) -> list[str]:
    if not scenarios.has_setup:
        return list(_NO_SETUP_LINES)

    probs = analysis.probabilities
    dominant = "bullish" if probs.bullish >= probs.bearish else "bearish"

    def scenario_block(side: str, icon: str, label: str, data: dict[str, str | None]) -> list[str]:
        suffix = " · основной" if side == dominant else ""
        direction = "выше" if side == "bullish" else "ниже"
        return [
            f"{icon} <b>{label}</b>{suffix}",
            f"   Вход:               {direction} {data['trigger']} ₽",
            f"   Цель 1:             {data.get('target_1') or '—'} ₽",
            f"   Цель 2:             {data.get('target_2') or '—'} ₽",
            f"   ❌ Отмена сценария: {data.get('invalidation') or '—'} ₽",
        ]

    # Show the dominant scenario first.
    order = [
        ("bullish", "🟢", "БЫЧИЙ", scenarios.bullish),
        ("bearish", "🔴", "МЕДВЕЖИЙ", scenarios.bearish),
    ]
    order.sort(key=lambda o: 0 if o[0] == dominant else 1)

    lines: list[str] = []
    for side, icon, label, data in order:
        if not data.get("trigger"):
            continue
        if lines:
            lines.append("")
        lines.extend(scenario_block(side, icon, label, data))
    return lines


def _risk_reward_lines(
    analysis: AnalysisResult,
    price: Decimal | None,
    decimals: int,
) -> list[str]:
    rr = compute_risk_reward(analysis, price, decimals)
    side = rr.get("side")
    if side is None:
        return ["❌ Недостаточно данных"]
    side_icon = "🟢" if side == "bullish" else "🔴"
    side_label = "Бычий" if side == "bullish" else "Медвежий"
    ratio = rr.get("ratio")
    return [
        f"Сторона:             {side_icon} {side_label}",
        f"💰 Вход:               {rr.get('entry', '—')} ₽",
        f"🛑 Стоп-лосс:          {rr.get('stop_loss', '—')} ₽",
        f"🎯 Цель:               {rr.get('target', '—')} ₽",
        f"📊 Соотношение:        {ratio if ratio else '—'}",
    ]


def _confidence_header(analysis: AnalysisResult) -> str:
    breakdown = compute_confidence_breakdown(analysis)
    total = round(breakdown["total"])
    return f"💪 <b>НАДЁЖНОСТЬ СИГНАЛА: {total}%</b>"


def _confidence_lines(analysis: AnalysisResult, *, detailed: bool) -> list[str]:
    if not detailed:
        return []
    breakdown = compute_confidence_breakdown(analysis)
    lines: list[str] = []
    for key, label in (
        ("trend", "Тренд"),
        ("structure", "Структура"),
        ("volume", "Объём"),
        ("volatility", "Волатильность"),
        ("probability", "Вероятность"),
    ):
        score = breakdown[key]
        weight = COMPONENT_WEIGHTS[key]
        weighted = round(score * weight, 1)
        lines.append(
            f"   {label}:            {fmt_percent(score / 100.0, places=0)} "
            f"(+{fmt_percent(weighted / 100.0, places=1)} в общий)"
        )
    return lines


def _horizons_lines(analysis: AnalysisResult) -> list[str]:
    horizons = compute_horizons(analysis)
    lines: list[str] = []
    for label, h in (("24ч", "24h"), ("48ч", "48h"), ("7д", "7d")):
        data = horizons[h]
        lines.append(
            f"{label}:  "
            f"🟢 {fmt_percent(data['bullish'])}  "
            f"🔴 {fmt_percent(data['bearish'])}  "
            f"🟡 {fmt_percent(data['sideways'])}"
        )
    return lines


def _conclusion_line(analysis: AnalysisResult, price: Decimal | None) -> str:
    conclusion = compute_conclusion(analysis, price)
    return escape(conclusion)


def _why_lines(analysis: AnalysisResult, price: Decimal | None) -> list[str]:
    return [f"• {escape(reason)}" for reason in compute_reasoning(analysis, price)]
