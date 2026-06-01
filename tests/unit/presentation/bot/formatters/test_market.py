"""Unit tests for the market / ranking formatters."""

from __future__ import annotations

from moex_analyst.presentation.bot.formatters import (
    format_market_overview,
    format_ranking,
)
from tests.unit.presentation.bot.formatters.conftest import make_market_overview


class TestMarketOverview:
    def test_lists_all_instruments_ranked(self) -> None:
        text = format_market_overview(make_market_overview())
        assert "Market overview" in text
        for ticker in ("SNGS", "VTBR", "SGZH"):
            assert ticker in text
        # Ranked best-first: numbering 1..3 present.
        assert "1." in text
        assert "2." in text
        assert "3." in text

    def test_best_first_ordering(self) -> None:
        text = format_market_overview(make_market_overview())
        # SNGS has the highest bullish score, so it should appear before SGZH.
        assert text.index("SNGS") < text.index("SGZH")

    def test_failed_tickers_noted(self) -> None:
        text = format_market_overview(make_market_overview(failed=("UWGN",)))
        assert "Unavailable" in text
        assert "UWGN" in text

    def test_empty_overview_message(self) -> None:
        text = format_market_overview(make_market_overview(tickers=()))
        assert "No instruments" in text


class TestRanking:
    def test_best_takes_top_n(self) -> None:
        text = format_ranking(make_market_overview(), best=True, limit=2)
        assert "Top 2 bullish" in text
        # Best two are SNGS then VTBR; SGZH excluded.
        assert "SNGS" in text
        assert "VTBR" in text
        assert "SGZH" not in text

    def test_worst_takes_bottom_n_most_bearish_first(self) -> None:
        text = format_ranking(make_market_overview(), best=False, limit=2)
        assert "Top 2 bearish" in text
        # Most bearish (SGZH) should rank #1 in the bearish list, before VTBR.
        assert text.index("SGZH") < text.index("VTBR")

    def test_empty_ranking_message(self) -> None:
        text = format_ranking(make_market_overview(tickers=()), best=True)
        assert "No instruments" in text
