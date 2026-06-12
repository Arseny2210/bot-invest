from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

from moex_analyst.application.services import ForecastTrackingService
from moex_analyst.application.use_cases import MarketOverviewUseCase, WatchlistUseCase
from moex_analyst.core.settings import Settings
from moex_analyst.presentation.bot.callbacks import MenuAction, MenuCallback
from moex_analyst.presentation.bot.handlers.overview import (
    cb_menu,
    cb_refresh_market,
    cb_refresh_signals,
    cmd_best,
    cmd_market,
    cmd_watchlist,
    cmd_worst,
)
from tests.unit.presentation.bot.formatters.conftest import (
    make_market_overview,
    make_watchlist,
)


def _bad_request(message: str) -> TelegramBadRequest:
    return TelegramBadRequest(method=MagicMock(), message=message)


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


@pytest.fixture
def forecast_service() -> AsyncMock:
    svc = AsyncMock(spec=ForecastTrackingService)
    svc.calculate_metrics = AsyncMock(return_value=None)
    return svc


@pytest.fixture
def settings() -> MagicMock:
    cfg = MagicMock(spec=Settings)
    bot_cfg = MagicMock()
    bot_cfg.notification_chat_id = 12345
    bot_cfg.rate_limit_per_minute = 20
    cfg.bot = bot_cfg
    cfg.environment = "test"
    return cfg


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
        assert "ОБЗОР РЫНКА" in text


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
        assert "БЫЧЬИХ" in text or "ТОП" in text


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
        assert "МЕДВЕЖЬИХ" in text or "ТОП" in text


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
        assert "СПИСОК ОТСЛЕЖИВАНИЯ" in text

    async def test_includes_watchlist_keyboard(
        self,
        mock_message: MagicMock,
        watchlist_use_case: AsyncMock,
    ) -> None:
        await cmd_watchlist(mock_message, watchlist_use_case)

        kwargs = mock_message.answer.call_args.kwargs
        assert "reply_markup" in kwargs


class TestCbMenu:
    @pytest.fixture
    def state(self) -> AsyncMock:
        return AsyncMock(spec=FSMContext)

    @pytest.mark.parametrize(
        ("action", "expected_in_text"),
        [
            (MenuAction.MARKET, "ОБЗОР РЫНКА"),
            (MenuAction.BEST, "БЫЧЬИХ"),
            (MenuAction.WORST, "МЕДВЕЖЬИХ"),
            (MenuAction.WATCHLIST, "СПИСОК ОТСЛЕЖИВАНИЯ"),
        ],
    )
    async def test_dispatches_overview_actions(
        self,
        mock_callback: MagicMock,
        market_use_case: AsyncMock,
        watchlist_use_case: AsyncMock,
        forecast_service: AsyncMock,
        settings: MagicMock,
        state: AsyncMock,
        action: MenuAction,
        expected_in_text: str,
    ) -> None:
        callback_data = MenuCallback(action=action)

        await cb_menu(
            mock_callback,
            callback_data,
            market_use_case,
            watchlist_use_case,
            forecast_service,
            settings,
            state,
        )

        mock_callback.message.edit_text.assert_awaited_once()
        text = mock_callback.message.edit_text.call_args[0][0]
        assert expected_in_text in text
        mock_callback.answer.assert_awaited_once()

    async def test_help_action(
        self,
        mock_callback: MagicMock,
        market_use_case: AsyncMock,
        watchlist_use_case: AsyncMock,
        forecast_service: AsyncMock,
        settings: MagicMock,
        state: AsyncMock,
    ) -> None:
        callback_data = MenuCallback(action=MenuAction.HELP)

        await cb_menu(
            mock_callback,
            callback_data,
            market_use_case,
            watchlist_use_case,
            forecast_service,
            settings,
            state,
        )

        mock_callback.message.edit_text.assert_awaited_once()
        text = mock_callback.message.edit_text.call_args[0][0]
        assert "Разделы" in text
        mock_callback.answer.assert_awaited_once()

    async def test_signals_action(
        self,
        mock_callback: MagicMock,
        market_use_case: AsyncMock,
        watchlist_use_case: AsyncMock,
        forecast_service: AsyncMock,
        settings: MagicMock,
        state: AsyncMock,
    ) -> None:
        callback_data = MenuCallback(action=MenuAction.SIGNALS)

        await cb_menu(
            mock_callback,
            callback_data,
            market_use_case,
            watchlist_use_case,
            forecast_service,
            settings,
            state,
        )

        mock_callback.message.edit_text.assert_awaited_once()
        text = mock_callback.message.edit_text.call_args[0][0]
        assert "СИГНАЛЫ" in text
        mock_callback.answer.assert_awaited_once()

    async def test_statistics_action(
        self,
        mock_callback: MagicMock,
        market_use_case: AsyncMock,
        watchlist_use_case: AsyncMock,
        forecast_service: AsyncMock,
        settings: MagicMock,
        state: AsyncMock,
    ) -> None:
        callback_data = MenuCallback(action=MenuAction.STATISTICS)

        await cb_menu(
            mock_callback,
            callback_data,
            market_use_case,
            watchlist_use_case,
            forecast_service,
            settings,
            state,
        )

        mock_callback.message.edit_text.assert_awaited_once()
        text = mock_callback.message.edit_text.call_args[0][0]
        assert "ТОЧНОСТЬ ПРОГНОЗОВ" in text
        mock_callback.answer.assert_awaited_once()

    async def test_settings_action(
        self,
        mock_callback: MagicMock,
        market_use_case: AsyncMock,
        watchlist_use_case: AsyncMock,
        forecast_service: AsyncMock,
        settings: MagicMock,
        state: AsyncMock,
    ) -> None:
        callback_data = MenuCallback(action=MenuAction.SETTINGS)

        await cb_menu(
            mock_callback,
            callback_data,
            market_use_case,
            watchlist_use_case,
            forecast_service,
            settings,
            state,
        )

        mock_callback.message.edit_text.assert_awaited_once()
        text = mock_callback.message.edit_text.call_args[0][0]
        assert "НАСТРОЙКИ" in text
        mock_callback.answer.assert_awaited_once()

    async def test_main_menu_action(
        self,
        mock_callback: MagicMock,
        market_use_case: AsyncMock,
        watchlist_use_case: AsyncMock,
        forecast_service: AsyncMock,
        settings: MagicMock,
        state: AsyncMock,
    ) -> None:
        callback_data = MenuCallback(action=MenuAction.MAIN_MENU)

        await cb_menu(
            mock_callback,
            callback_data,
            market_use_case,
            watchlist_use_case,
            forecast_service,
            settings,
            state,
        )

        mock_callback.message.edit_text.assert_awaited_once()
        state.clear.assert_awaited_once()
        mock_callback.answer.assert_awaited_once()

    async def test_watchlist_includes_keyboard(
        self,
        mock_callback: MagicMock,
        market_use_case: AsyncMock,
        watchlist_use_case: AsyncMock,
        forecast_service: AsyncMock,
        settings: MagicMock,
        state: AsyncMock,
    ) -> None:
        callback_data = MenuCallback(action=MenuAction.WATCHLIST)

        await cb_menu(
            mock_callback,
            callback_data,
            market_use_case,
            watchlist_use_case,
            forecast_service,
            settings,
            state,
        )

        kwargs = mock_callback.message.edit_text.call_args.kwargs
        assert "reply_markup" in kwargs


# ---------------------------------------------------------------------------
# Refresh (🔄) — must edit the existing message, never send a duplicate
# ---------------------------------------------------------------------------


class TestRefreshSingleMessage:
    async def test_market_refresh_edits_in_place(
        self, mock_callback: MagicMock, market_use_case: AsyncMock
    ) -> None:
        await cb_refresh_market(mock_callback, market_use_case)

        mock_callback.message.edit_text.assert_awaited_once()
        mock_callback.message.answer.assert_not_awaited()
        mock_callback.answer.assert_awaited_once()

    async def test_signals_refresh_edits_in_place(
        self, mock_callback: MagicMock, market_use_case: AsyncMock
    ) -> None:
        await cb_refresh_signals(mock_callback, market_use_case)

        mock_callback.message.edit_text.assert_awaited_once()
        mock_callback.message.answer.assert_not_awaited()

    async def test_unchanged_content_does_not_duplicate(
        self, mock_callback: MagicMock, market_use_case: AsyncMock
    ) -> None:
        # Identical data → "message is not modified" → must NOT resend.
        mock_callback.message.edit_text.side_effect = _bad_request(
            "Bad Request: message is not modified"
        )

        await cb_refresh_market(mock_callback, market_use_case)

        mock_callback.message.answer.assert_not_awaited()

    async def test_real_edit_failure_does_not_create_new_message(
        self, mock_callback: MagicMock, market_use_case: AsyncMock
    ) -> None:
        """edit_or_answer must NOT fall back to a new message on edit failure."""
        mock_callback.message.edit_text.side_effect = _bad_request(
            "Bad Request: message to edit not found"
        )

        await cb_refresh_market(mock_callback, market_use_case)

        mock_callback.message.answer.assert_not_awaited()
