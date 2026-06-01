"""Dependency-injection composition root (dishka)."""

from __future__ import annotations

from moex_analyst.di.container import make_container
from moex_analyst.di.providers import AppProvider

__all__ = ["AppProvider", "make_container"]
