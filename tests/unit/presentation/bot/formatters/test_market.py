"""Unit tests for the market / ranking formatters."""

from __future__ import annotations

from moex_analyst.presentation.bot.formatters import (
    format_market_overview,
    format_ranking,
)
from moex_analyst.presentation.bot.formatters.text import fmt_instrument_name
from tests.unit.presentation.bot.formatters.conftest import make_market_overview


class TestMarketOverview:
    def test_lists_all_instruments_ranked(self) -> None:
        text = format_market_overview(make_market_overview())
        assert "ОБЗОР РЫНКА" in text
        assert fmt_instrument_name("SNGS") in text
        assert fmt_instrument_name("SGZH") in text
        # Ranked best-first: numbering present for visible instruments.
        assert "1." in text

    def test_best_first_ordering(self) -> None:
        text = format_market_overview(make_market_overview())
        # SNGS has the highest bullish score, so it should appear before SGZH.
        assert text.index(fmt_instrument_name("SNGS")) < text.index(fmt_instrument_name("SGZH"))

    def test_failed_tickers_noted(self) -> None:
        text = format_market_overview(make_market_overview(failed=("UWGN",)))
        assert "Нет данных" in text
        assert "UWGN" in text

    def test_empty_overview_message(self) -> None:
        text = format_market_overview(make_market_overview(tickers=()))
        assert "Нет инструментов" in text


class TestRanking:
    def test_best_takes_top_n(self) -> None:
        text = format_ranking(make_market_overview(), best=True, limit=2)
        assert "ТОП-2 БЫЧЬИХ" in text
        # Best two are SNGS then VTBR; SGZH excluded.
        assert fmt_instrument_name("SNGS") in text
        assert fmt_instrument_name("VTBR") in text
        assert fmt_instrument_name("SGZH") not in text

    def test_worst_takes_bottom_n_most_bearish_first(self) -> None:
        text = format_ranking(make_market_overview(), best=False, limit=2)
        assert "ТОП-2 МЕДВЕЖЬИХ" in text
        # Most bearish (SGZH) should rank #1 in the bearish list, before VTBR.
        assert text.index(fmt_instrument_name("SGZH")) < text.index(fmt_instrument_name("VTBR"))

    def test_empty_ranking_message(self) -> None:
        text = format_ranking(make_market_overview(tickers=()), best=True)
        assert "Нет инструментов" in text
