"""Formatters for the market views — ``/market``, ``/best``, ``/worst``.

Pure: :class:`MarketOverview` → HTML string. The same ranked overview powers all
three commands; the ranking formatter just slices the top/bottom N.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from moex_analyst.presentation.bot.formatters.text import (
    escape,
    fmt_percent,
    fmt_score,
    trend_icon,
)

if TYPE_CHECKING:
    from moex_analyst.application.use_cases.dto import MarketOverview, ScoredInstrument

__all__ = ["format_market_overview", "format_ranking"]

_DEFAULT_TOP_N = 3


def format_market_overview(overview: MarketOverview) -> str:
    """Render every tracked instrument, ranked best-first."""
    header = f"🗺 <b>Market overview</b> <i>({escape(overview.timeframe.value)})</i>"
    if not overview.scored:
        return f"{header}\n\n⚠️ No instruments could be analysed right now."

    rows = [_row(i, item) for i, item in enumerate(overview.scored, start=1)]
    return "\n".join([header, "", *rows, _footer(overview)])


def format_ranking(
    overview: MarketOverview,
    *,
    best: bool,
    limit: int = _DEFAULT_TOP_N,
) -> str:
    """Render the top (``best=True``) or bottom (``best=False``) ``limit`` names."""
    if best:
        header = f"🏆 <b>Top {limit} bullish</b> <i>({escape(overview.timeframe.value)})</i>"
        selection = list(overview.scored[:limit])
    else:
        header = f"🐻 <b>Top {limit} bearish</b> <i>({escape(overview.timeframe.value)})</i>"
        # Weakest first: take the tail, then reverse so #1 is the most bearish.
        selection = list(reversed(overview.scored[-limit:]))

    if not selection:
        return f"{header}\n\n⚠️ No instruments could be analysed right now."

    rows = [_row(i, item) for i, item in enumerate(selection, start=1)]
    return "\n".join([header, "", *rows, _footer(overview)])


def _row(rank: int, item: ScoredInstrument) -> str:
    analysis = item.analysis
    trend = analysis.trend
    alert_note = f" · {item.alert_count}⚡" if item.alert_count else ""
    return (
        f"{rank}. {trend_icon(trend.direction)} <b>{escape(analysis.ticker)}</b> "
        f"score {fmt_score(item.score)} "
        f"(↑{fmt_percent(analysis.probabilities.bullish, places=0)} / "
        f"↓{fmt_percent(analysis.probabilities.bearish, places=0)}){alert_note}"
    )


def _footer(overview: MarketOverview) -> str:
    if not overview.failed:
        return ""
    failed = ", ".join(escape(t) for t in overview.failed)
    return f"\n<i>Unavailable: {failed}</i>"
