"""Container factory — the composition root.

Builds the dishka :class:`AsyncContainer` from :class:`AppProvider`, injecting
the live :class:`Settings` as context. Entry points create the container once at
startup and close it on shutdown.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dishka import make_async_container

from moex_analyst.core.settings import Settings
from moex_analyst.di.providers import AppProvider

if TYPE_CHECKING:
    from dishka import AsyncContainer

__all__ = ["make_container"]


def make_container(settings: Settings) -> AsyncContainer:
    """Create the application's async DI container."""
    return make_async_container(AppProvider(), context={Settings: settings})
