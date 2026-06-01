"""Static / templated formatters: start, help and user-facing error messages."""

from __future__ import annotations

from moex_analyst.presentation.bot.formatters.text import escape

__all__ = ["format_error", "format_help", "format_start"]


def format_start(first_name: str | None = None) -> str:
    """Welcome message shown for ``/start``."""
    greeting = f"Hi {escape(first_name)}! " if first_name else "Hi! "
    return (
        f"👋 <b>{greeting}I'm the MOEX market analyst.</b>\n\n"
        "I run a deterministic technical analysis (trend, structure, "
        "support/resistance, RSI/EMA/ATR) over Moscow Exchange instruments and "
        "raise actionable alerts.\n\n"
        "Use the buttons below or send /help to see every command."
    )


def format_help() -> str:
    """Command reference shown for ``/help``."""
    return (
        "🛟 <b>Commands</b>\n\n"
        "• /analyze &lt;ticker&gt; — full analysis of one instrument "
        "(e.g. <code>/analyze SNGS</code>, optionally <code>/analyze SNGS 1H</code>)\n"
        "• /market — ranked overview of all tracked instruments\n"
        "• /best — most bullish instruments right now\n"
        "• /worst — most bearish instruments right now\n"
        "• /watchlist — the instruments I track\n"
        "• /help — this message\n\n"
        "<i>Timeframes: 1H, 4H, 1D (default 1D).</i>"
    )


def format_error(message: str) -> str:
    """Wrap a user-facing error message (already plain, will be escaped)."""
    return f"⚠️ {escape(message)}"
