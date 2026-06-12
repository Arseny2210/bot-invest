from __future__ import annotations

from aiogram import Router

from moex_analyst.presentation.bot.handlers import (
    analyze,
    overview,
    signals,
    start_help,
)
from moex_analyst.presentation.bot.handlers import (
    settings as settings_router,
)

__all__ = ["build_root_router"]


def build_root_router() -> Router:
    root = Router(name="root")
    root.include_router(start_help.router)
    root.include_router(analyze.router)
    root.include_router(overview.router)
    root.include_router(signals.router)
    root.include_router(settings_router.router)
    return root
