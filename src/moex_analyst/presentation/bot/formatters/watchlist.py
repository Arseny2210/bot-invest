"""Formatter for ``/watchlist`` — the tracked-instrument list."""

from __future__ import annotations

from typing import TYPE_CHECKING

from moex_analyst.presentation.bot.formatters.text import fmt_instrument_name, section_divider

if TYPE_CHECKING:
    from moex_analyst.application.use_cases.dto import Watchlist

__all__ = ["format_watchlist"]

_MARKET_LABELS = {"index": "📐 Индекс", "shares": "🏢 Акция"}


def format_watchlist(watchlist: Watchlist) -> str:
    lines: list[str] = [
        section_divider(),
        "⭐ <b>СПИСОК ОТСЛЕЖИВАНИЯ</b>",
        section_divider(),
        "",
    ]

    if not watchlist.instruments:
        lines.append("📭 Список пуст")
        lines.append("")
        lines.append(section_divider())
        return "\n".join(lines)

    for inst in watchlist.instruments:
        label = _MARKET_LABELS.get(inst.market_type.value, "📌")
        lines.append(f"{label}  <b>{fmt_instrument_name(inst.ticker)}</b>")

    lines.extend(
        [
            "",
            section_divider(),
            "💡 <i>Нажми кнопку ниже или отправь /analyze &lt;тикер&gt;</i>",
            section_divider(),
        ]
    )
    return "\n".join(lines)
