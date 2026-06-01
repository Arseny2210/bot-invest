"""Bot process entry point — long-polling only (no webhook).

Wires settings, logging and the dishka container into an Aiogram dispatcher,
registers the middlewares and routers, publishes the command menu and runs the
polling loop. Console script: ``moex-bot`` (see ``pyproject.toml``).
"""

from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dishka.integrations.aiogram import setup_dishka
from loguru import logger

from moex_analyst.core.logging import configure_logging
from moex_analyst.core.settings import get_settings
from moex_analyst.di import make_container
from moex_analyst.presentation.bot.commands import set_bot_commands
from moex_analyst.presentation.bot.middlewares import (
    LoggingMiddleware,
    ThrottlingMiddleware,
)
from moex_analyst.presentation.bot.routers import build_root_router

__all__ = ["main", "run"]


async def main() -> None:
    """Configure and run the bot until interrupted."""
    settings = get_settings()
    configure_logging(settings, service="bot")
    log = logger.bind(service="bot")

    if settings.bot.use_webhook:
        log.warning(
            "BOT__USE_WEBHOOK is enabled, but this process runs polling only; "
            "ignoring webhook settings.",
        )

    container = make_container(settings)
    bot = Bot(
        token=settings.bot.token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(build_root_router())

    # Cross-cutting middlewares (one throttler instance shared across observers
    # so a user's per-minute budget covers both messages and callbacks).
    logging_mw = LoggingMiddleware()
    throttle_mw = ThrottlingMiddleware(settings.bot.rate_limit_per_minute)
    for observer in (dp.message, dp.callback_query):
        observer.middleware(logging_mw)
        observer.middleware(throttle_mw)

    setup_dishka(container, dp, auto_inject=True)

    try:
        await set_bot_commands(bot)
        await bot.delete_webhook(drop_pending_updates=True)
        log.info("Bot polling started")
        await dp.start_polling(bot)
    finally:
        await container.close()
        await bot.session.close()
        log.info("Bot stopped")


def run() -> None:
    """Synchronous console-script entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
