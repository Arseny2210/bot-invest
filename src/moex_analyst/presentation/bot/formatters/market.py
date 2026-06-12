"""Formatters for the market views — ``/market``, ``/best``, ``/worst``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from moex_analyst.presentation.bot.formatters.text import (
    escape,
    fmt_freshness_block,
    fmt_instrument_name,
    fmt_percent,
    fmt_score,
    section_divider,
    trend_icon,
)

if TYPE_CHECKING:
    from moex_analyst.application.use_cases.dto import MarketOverview, ScoredInstrument

__all__ = ["format_market_overview", "format_ranking"]

_DEFAULT_TOP_N = 3

_BULLISH_THRESHOLD = 0.1
_BEARISH_THRESHOLD = -0.1


def format_market_overview(overview: MarketOverview) -> str:
    tf = escape(overview.timeframe.value)
    lines: list[str] = [
        section_divider(),
        "🗺 <b>ОБЗОР РЫНКА</b>",
        section_divider(),
        "",
        f"⏰ Таймфрейм:          {tf}",
        "",
    ]

    if not overview.scored:
        lines.append("⚠️ Нет инструментов для анализа.")
        return "\n".join(lines)

    bullish = [s for s in overview.scored if s.score >= _BULLISH_THRESHOLD]
    bearish = [s for s in overview.scored if s.score <= _BEARISH_THRESHOLD]
    neutral = [s for s in overview.scored if _BEARISH_THRESHOLD < s.score < _BULLISH_THRESHOLD]

    lines.append(section_divider())
    lines.append("📈 <b>ЛИДЕРЫ РОСТА</b>")
    lines.append(section_divider())
    lines.append("")
    if bullish:
        for i, item in enumerate(bullish, start=1):
            lines.append(f"{i}. {_overview_row(item)}")
    else:
        lines.append("   Нет")
    lines.append("")

    lines.append(section_divider())
    lines.append("📉 <b>ЛИДЕРЫ ПАДЕНИЯ</b>")
    lines.append(section_divider())
    lines.append("")
    if bearish:
        for i, item in enumerate(reversed(bearish), start=1):
            lines.append(f"{i}. {_overview_row(item)}")
    else:
        lines.append("   Нет")
    lines.append("")

    lines.append(section_divider())
    lines.append("🏛 <b>ИНДЕКС МОСБИРЖИ</b>")
    lines.append(section_divider())
    lines.append("")
    imoex_items = [s for s in overview.scored if s.analysis.ticker == "IMOEX"]
    if imoex_items:
        imoex = imoex_items[0]
        a = imoex.analysis
        trend_dir = (
            "восходящий"
            if a.trend.direction.value == "up"
            else "нисходящий"
            if a.trend.direction.value == "down"
            else "боковик"
        )
        imoex_label = fmt_instrument_name("IMOEX")
        score = fmt_score(imoex.score)
        lines.append(f"   {trend_icon(a.trend.direction)} {imoex_label}: {trend_dir} ({score})")
    else:
        lines.append("   Нет данных")
    lines.append("")

    lines.append(section_divider())
    lines.append("📊 <b>НАСТРОЕНИЕ РЫНКА</b>")
    lines.append(section_divider())
    lines.append("")
    lines.append(f"   🟢 Бычьих:             {len(bullish)}")
    lines.append(f"   🔴 Медвежьих:          {len(bearish)}")
    lines.append(f"   🟡 Нейтральных:        {len(neutral)}")
    if len(bullish) > len(bearish):
        sentiment = "🟢 Бычье настроение"
    elif len(bearish) > len(bullish):
        sentiment = "🔴 Медвежье настроение"
    else:
        sentiment = "🟡 Нейтральное настроение"
    lines.append(f"   Преобладает:          {sentiment}")
    lines.append("")

    avg_bullish = sum(s.analysis.probabilities.bullish for s in overview.scored) / len(
        overview.scored
    )
    lines.append(section_divider())
    lines.append("🎯 <b>ОБЩАЯ ВЕРОЯТНОСТЬ РОСТА</b>")
    lines.append(section_divider())
    lines.append("")
    lines.append(f"   Средняя:              {fmt_percent(avg_bullish)}")
    lines.append("")

    if overview.failed:
        failed = ", ".join(escape(t) for t in overview.failed)
        lines.append(f"⚠️ Нет данных: {failed}")
        lines.append("")

    lines.append(section_divider())
    as_of = overview.scored[0].analysis.as_of
    lines.append(fmt_freshness_block(as_of, overview.timeframe))
    lines.append(section_divider())

    return "\n".join(lines)


def format_ranking(
    overview: MarketOverview,
    *,
    best: bool,
    limit: int = _DEFAULT_TOP_N,
) -> str:
    if best:
        header_icon = "🏆"
        header_title = f"ТОП-{limit} БЫЧЬИХ"
        selection = list(overview.scored[:limit])
    else:
        header_icon = "🐻"
        header_title = f"ТОП-{limit} МЕДВЕЖЬИХ"
        selection = list(reversed(overview.scored[-limit:]))

    lines: list[str] = [
        section_divider(),
        f"{header_icon} <b>{header_title}</b>",
        section_divider(),
        "",
    ]

    if not selection:
        lines.append("⚠️ Нет инструментов для анализа.")
        return "\n".join(lines)

    for i, item in enumerate(selection, start=1):
        lines.append(f"{i}. {_ranking_row(item)}")
    lines.append("")

    if overview.failed:
        failed = ", ".join(escape(t) for t in overview.failed)
        lines.append(f"⚠️ Нет данных: {failed}")
        lines.append("")

    lines.append(section_divider())
    as_of = overview.scored[0].analysis.as_of
    tf = escape(overview.timeframe.value)
    lines.append(f"⏰ Таймфрейм:          {tf}")
    lines.append(fmt_freshness_block(as_of, overview.timeframe))
    lines.append(section_divider())

    return "\n".join(lines)


def _overview_row(item: ScoredInstrument) -> str:
    a = item.analysis
    return (
        f"{trend_icon(a.trend.direction)} <b>{fmt_instrument_name(a.ticker)}</b>  "
        f"{fmt_score(item.score)}  "
        f"(↑{fmt_percent(a.probabilities.bullish, places=0)} / "
        f"↓{fmt_percent(a.probabilities.bearish, places=0)})"
    )


def _ranking_row(item: ScoredInstrument) -> str:
    a = item.analysis
    alert_note = f" ⚡{item.alert_count}" if item.alert_count else ""
    return (
        f"{trend_icon(a.trend.direction)} <b>{fmt_instrument_name(a.ticker)}</b>  "
        f"{fmt_score(item.score)}  "
        f"(↑{fmt_percent(a.probabilities.bullish, places=0)} / "
        f"↓{fmt_percent(a.probabilities.bearish, places=0)}){alert_note}"
    )
