"""Unit tests for the watchlist and static (start/help/error) formatters."""

from __future__ import annotations

from moex_analyst.presentation.bot.formatters import (
    format_error,
    format_help,
    format_start,
    format_watchlist,
)
from tests.unit.presentation.bot.formatters.conftest import make_watchlist


class TestWatchlist:
    def test_lists_tracked_instruments(self) -> None:
        text = format_watchlist(make_watchlist())
        assert "Watchlist" in text
        assert "IMOEX" in text
        assert "SNGS" in text

    def test_analyze_hint_is_html_escaped(self) -> None:
        # The hint mentions "/analyze <ticker>" — the angle brackets must be escaped.
        text = format_watchlist(make_watchlist())
        assert "&lt;ticker&gt;" in text


class TestStartHelp:
    def test_start_greets_named_user(self) -> None:
        assert "Alice" in format_start("Alice")

    def test_start_without_name(self) -> None:
        text = format_start(None)
        assert "Hi!" in text

    def test_start_escapes_name(self) -> None:
        assert "&lt;b&gt;" in format_start("<b>")

    def test_help_lists_every_command(self) -> None:
        text = format_help()
        for command in ("/analyze", "/market", "/best", "/worst", "/watchlist", "/help"):
            assert command in text


class TestError:
    def test_error_prefixed_and_escaped(self) -> None:
        text = format_error("bad ticker <x> & co")
        assert text.startswith("⚠️")
        assert "&lt;x&gt;" in text
        assert "&amp;" in text
