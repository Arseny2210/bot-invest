"""FastAPI application — health and webhook endpoints.

Console script: ``moex-api`` (see ``pyproject.toml``).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from loguru import logger

from moex_analyst.core.logging import configure_logging
from moex_analyst.core.settings import get_settings
from moex_analyst.presentation.api.router import api_router

__all__ = ["create_app", "run"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    log = logger.bind(service="api")
    log.info("API starting")
    try:
        yield
    finally:
        log.info("API stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings, service="api")

    app = FastAPI(
        title="MOEX AI Analyst API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.include_router(api_router)
    return app


def run() -> None:
    uvicorn.run(
        "moex_analyst.main:create_app",
        host="0.0.0.0",
        port=8000,
        factory=True,
        reload=False,
        log_config=None,
    )
