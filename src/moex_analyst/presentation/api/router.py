"""API routes — health and readiness probes for container orchestration."""

from __future__ import annotations

from fastapi import APIRouter

__all__ = ["api_router"]

api_router = APIRouter()


@api_router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@api_router.get("/ready")
async def ready() -> dict[str, str]:
    return {"status": "ready"}
