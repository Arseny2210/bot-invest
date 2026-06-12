from aiogram import Router

from moex_analyst.presentation.bot.handlers import analyze, overview, settings, signals, start_help
from moex_analyst.presentation.bot.routers import build_root_router


class TestBuildRootRouter:
    """build_root_router uses module-level router singletons that can only be
    attached once (Aiogram prevents re-attachment). All assertions share the
    same root router instance to avoid RuntimeError on duplicate calls."""

    _root = build_root_router()

    def test_returns_a_router(self) -> None:
        assert isinstance(self._root, Router)

    def test_named_root(self) -> None:
        assert self._root.name == "root"

    def test_includes_start_help_router(self) -> None:
        assert start_help.router in self._root.sub_routers

    def test_includes_analyze_router(self) -> None:
        assert analyze.router in self._root.sub_routers

    def test_includes_overview_router(self) -> None:
        assert overview.router in self._root.sub_routers

    def test_includes_signals_router(self) -> None:
        assert signals.router in self._root.sub_routers

    def test_includes_settings_router(self) -> None:
        assert settings.router in self._root.sub_routers

    def test_has_exactly_five_sub_routers(self) -> None:
        assert len(list(self._root.sub_routers)) == 5
