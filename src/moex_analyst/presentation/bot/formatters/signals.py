from __future__ import annotations

from typing import TYPE_CHECKING

from moex_analyst.presentation.bot.formatters.text import (
    fmt_freshness_block,
    fmt_instrument_name,
    fmt_percent,
    fmt_score,
    section_divider,
    trend_icon,
)

if TYPE_CHECKING:
    from moex_analyst.application.use_cases.dto import MarketOverview

__all__ = ["format_signals"]


def format_signals(overview: MarketOverview) -> str:
    lines: list[str] = [
        section_divider(),
        "🎯 <b>АКТИВНЫЕ СИГНАЛЫ</b>",
        section_divider(),
        "",
    ]

    alerted = [s for s in overview.scored if s.alert_count > 0]

    if not alerted:
        lines.append("✅ Нет активных сигналов")
        lines.append("")
        if overview.scored:
            as_of = overview.scored[0].analysis.as_of
            lines.append(fmt_freshness_block(as_of, overview.timeframe))
        lines.append(section_divider())
        return "\n".join(lines)

    for item in alerted:
        a = item.analysis
        lines.append(f"🚨 <b>{fmt_instrument_name(a.ticker)}</b> — {item.alert_count} сигнал(а)")
        lines.append(
            f"   {trend_icon(a.trend.direction)} "
            f"Оценка: {fmt_score(item.score)} · "
            f"↑{fmt_percent(a.probabilities.bullish, places=0)} / "
            f"↓{fmt_percent(a.probabilities.bearish, places=0)}"
        )
        lines.append("")

    lines.append(section_divider())
    as_of = overview.scored[0].analysis.as_of
    lines.append(fmt_freshness_block(as_of, overview.timeframe))
    lines.append(section_divider())
    lines.append("💡 <i>Нажми на тикер в Избранном для детального анализа</i>")
    lines.append(section_divider())

    return "\n".join(lines)
