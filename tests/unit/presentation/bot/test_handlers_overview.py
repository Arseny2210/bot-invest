from unittest.mock import AsyncMock, MagicMock

import pytest

from moex_analyst.application.use_cases import MarketOverviewUseCase, WatchlistUseCase
from moex_analyst.presentation.bot.callbacks import MenuAction, MenuCallback
from moex_analyst.presentation.bot.handlers.overview import (
    cb_menu,
    cmd_best,
    cmd_market,
    cmd_watchlist,
    cmd_worst,
)
from tests.unit.presentation.bot.formatters.conftest import (
    make_market_overview,
    make_watchlist,
)


@pytest.fixture
def market_use_case() -> AsyncMock:
    uc = AsyncMock(spec=MarketOverviewUseCase)
    uc.execute.return_value = make_market_overview()
    return uc


@pytest.fixture
def watchlist_use_case() -> AsyncMock:
    uc = AsyncMock(spec=WatchlistUseCase)
    uc.execute.return_value = make_watchlist()
    return uc


class TestCmdMarket:
    async def test_sends_market_overview(
        self,
        mock_message: MagicMock,
        market_use_case: AsyncMock,
    ) -> None:
        await cmd_market(mock_message, market_use_case)

        market_use_case.execute.assert_awaited_once()
        mock_message.answer.assert_awaited_once()
        text = mock_message.answer.call_args[0][0]
        assert "Market overview" in text


class TestCmdBest:
    async def test_sends_best_ranking(
        self,
        mock_message: MagicMock,
        market_use_case: AsyncMock,
    ) -> None:
        await cmd_best(mock_message, market_use_case)

        market_use_case.execute.assert_awaited_once()
        mock_message.answer.assert_awaited_once()
        text = mock_message.answer.call_args[0][0]
        assert "bullish" in text or "Best" in text or "Top" in text


class TestCmdWorst:
    async def test_sends_worst_ranking(
        self,
        mock_message: MagicMock,
        market_use_case: AsyncMock,
    ) -> None:
        await cmd_worst(mock_message, market_use_case)

        market_use_case.execute.assert_awaited_once()
        mock_message.answer.assert_awaited_once()
        text = mock_message.answer.call_args[0][0]
        assert "bearish" in text or "Worst" in text or "Top" in text


class TestCmdWatchlist:
    async def test_sends_watchlist(
        self,
        mock_message: MagicMock,
        watchlist_use_case: AsyncMock,
    ) -> None:
        await cmd_watchlist(mock_message, watchlist_use_case)

        watchlist_use_case.execute.assert_awaited_once()
        mock_message.answer.assert_awaited_once()
        text = mock_message.answer.call_args[0][0]
        assert "Watchlist" in text

    async def test_includes_watchlist_keyboard(
        self,
        mock_message: MagicMock,
        watchlist_use_case: AsyncMock,
    ) -> None:
        await cmd_watchlist(mock_message, watchlist_use_case)

        kwargs = mock_message.answer.call_args.kwargs
        assert "reply_markup" in kwargs


class TestCbMenu:
    @pytest.mark.parametrize(
        ("action", "expected_in_text"),
        [
            (MenuAction.MARKET, "Market overview"),
            (MenuAction.BEST, "bullish"),
            (MenuAction.WORST, "bearish"),
            (MenuAction.WATCHLIST, "Watchlist"),
        ],
    )
    async def test_dispatches_overview_actions(
        self,
        mock_callback: MagicMock,
        market_use_case: AsyncMock,
        watchlist_use_case: AsyncMock,
        action: MenuAction,
        expected_in_text: str,
    ) -> None:
        callback_data = MenuCallback(action=action)

        await cb_menu(mock_callback, callback_data, market_use_case, watchlist_use_case)

        mock_callback.message.answer.assert_awaited_once()
        text = mock_callback.message.answer.call_args[0][0]
        assert expected_in_text in text
        mock_callback.answer.assert_awaited_once()

    async def test_help_action(
        self,
        mock_callback: MagicMock,
        market_use_case: AsyncMock,
        watchlist_use_case: AsyncMock,
    ) -> None:
        callback_data = MenuCallback(action=MenuAction.HELP)

        await cb_menu(mock_callback, callback_data, market_use_case, watchlist_use_case)

        mock_callback.message.answer.assert_awaited_once()
        text = mock_callback.message.answer.call_args[0][0]
        assert "Commands" in text
        mock_callback.answer.assert_awaited_once()

    async def test_watchlist_includes_keyboard(
        self,
        mock_callback: MagicMock,
        market_use_case: AsyncMock,
        watchlist_use_case: AsyncMock,
    ) -> None:
        callback_data = MenuCallback(action=MenuAction.WATCHLIST)

        await cb_menu(mock_callback, callback_data, market_use_case, watchlist_use_case)

        kwargs = mock_callback.message.answer.call_args.kwargs
        assert "reply_markup" in kwargs
