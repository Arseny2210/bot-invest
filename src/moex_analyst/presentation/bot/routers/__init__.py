"""Router assembly — the single root router included by the dispatcher."""

from __future__ import annotations

from aiogram import Router

from moex_analyst.presentation.bot.handlers import analyze, overview, start_help

__all__ = ["build_root_router"]


def build_root_router() -> Router:
    """Compose every feature router under one root router."""
    root = Router(name="root")
    root.include_router(start_help.router)
    root.include_router(analyze.router)
    root.include_router(overview.router)
    return root
