"""Unit tests for the watchlist and static (start/help/error) formatters."""

from __future__ import annotations

from moex_analyst.presentation.bot.formatters import (
    format_error,
    format_help,
    format_start,
    format_watchlist,
)
from moex_analyst.presentation.bot.formatters.text import fmt_instrument_name
from tests.unit.presentation.bot.formatters.conftest import make_watchlist


class TestWatchlist:
    def test_lists_tracked_instruments(self) -> None:
        text = format_watchlist(make_watchlist())
        assert "СПИСОК ОТСЛЕЖИВАНИЯ" in text
        assert fmt_instrument_name("IMOEX") in text
        assert fmt_instrument_name("SNGS") in text

    def test_analyze_hint_is_html_escaped(self) -> None:
        # The hint mentions "/analyze <ticker>" — the angle brackets must be escaped.
        text = format_watchlist(make_watchlist())
        assert "&lt;тикер&gt;" in text


class TestStartHelp:
    def test_start_greets_named_user(self) -> None:
        assert "Alice" in format_start("Alice")

    def test_start_without_name(self) -> None:
        text = format_start(None)
        assert "Привет!" in text

    def test_start_escapes_name(self) -> None:
        assert "&lt;b&gt;" in format_start("<b>")

    def test_help_lists_sections(self) -> None:
        text = format_help()
        assert "Разделы" in text
        for section in ("Анализ акции", "Состояние рынка", "Избранное", "Сигналы"):
            assert section in text


class TestError:
    def test_error_prefixed_and_escaped(self) -> None:
        text = format_error("bad ticker <x> & co")
        assert text.startswith("⚠️")
        assert "&lt;x&gt;" in text
        assert "&amp;" in text
