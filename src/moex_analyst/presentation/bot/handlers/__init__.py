"""Update handlers, grouped by feature into per-module routers."""

from __future__ import annotations

from moex_analyst.presentation.bot.handlers import analyze, overview, start_help
from moex_analyst.presentation.bot.handlers.errors import friendly_error

__all__ = ["analyze", "friendly_error", "overview", "start_help"]
