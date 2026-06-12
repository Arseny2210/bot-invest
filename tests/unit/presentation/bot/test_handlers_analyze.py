from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandObject
from aiogram.fsm.context import FSMContext

from moex_analyst.application.use_cases import AnalyzeInstrumentUseCase
from moex_analyst.domain.market.timeframe import Timeframe
from moex_analyst.presentation.bot.callbacks import (
    AnalyzeCallback,
    AnalyzeTypeCallback,
    RefreshCallback,
    TickerCallback,
    TimeframeCallback,
)
from moex_analyst.presentation.bot.handlers.analyze import (
    AnalyzeFlow,
    _edit_or_answer,
    _parse_args,
    cb_analysis_type,
    cb_analyze,
    cb_back,
    cb_custom_ticker,
    cb_main_menu,
    cb_refresh_analysis,
    cb_start_analyze,
    cb_ticker,
    cb_timeframe,
    cmd_analyze,
    msg_custom_ticker,
)
from tests.unit.presentation.bot.formatters.conftest import make_instrument_analysis


def _bad_request(message: str) -> TelegramBadRequest:
    return TelegramBadRequest(method=MagicMock(), message=message)


# ---------------------------------------------------------------------------
# _parse_args
# ---------------------------------------------------------------------------


class TestParseArgs:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            (None, None),
            ("", None),
            ("   ", None),
            ("SNGS", ("SNGS", Timeframe.D1)),
            ("sngs", ("SNGS", Timeframe.D1)),
            ("SNGS 15M", ("SNGS", Timeframe.M15)),
            ("SNGS 1H", ("SNGS", Timeframe.H1)),
            ("SNGS H1", ("SNGS", Timeframe.H1)),
            ("SNGS 4H", ("SNGS", Timeframe.H4)),
            ("SNGS H4", ("SNGS", Timeframe.H4)),
            ("SNGS 1D", ("SNGS", Timeframe.D1)),
            ("SNGS D1", ("SNGS", Timeframe.D1)),
            ("SNGS DAY", ("SNGS", Timeframe.D1)),
            ("SNGS 1W", ("SNGS", Timeframe.W1)),
            ("SNGS W1", ("SNGS", Timeframe.W1)),
            ("SNGS WEEK", ("SNGS", Timeframe.W1)),
            ("SNGS invalid", ("SNGS", Timeframe.D1)),
            ("SNGS 1H extra", ("SNGS", Timeframe.H1)),
            ("vtbr 4h", ("VTBR", Timeframe.H4)),
        ],
    )
    def test_various_inputs(
        self,
        raw: str | None,
        expected: tuple[str, Timeframe] | None,
    ) -> None:
        assert _parse_args(raw) == expected


# ---------------------------------------------------------------------------
# cmd_analyze
# ---------------------------------------------------------------------------


class TestCmdAnalyze:
    async def test_no_args_sends_error(
        self, mock_message: MagicMock, mock_command: MagicMock
    ) -> None:
        mock_command.args = None
        use_case = AsyncMock(spec=AnalyzeInstrumentUseCase)
        state = AsyncMock(spec=FSMContext)

        await cmd_analyze(mock_message, mock_command, use_case, state)

        mock_message.answer.assert_awaited_once()
        text = mock_message.answer.call_args[0][0]
        assert "Выберите инструмент" in text
        use_case.execute.assert_not_awaited()
        state.clear.assert_awaited_once()

    async def test_valid_args_calls_use_case(self, mock_message: MagicMock) -> None:
        command = MagicMock(spec=CommandObject)
        command.args = "SNGS"
        use_case = AsyncMock(spec=AnalyzeInstrumentUseCase)
        use_case.execute.return_value = make_instrument_analysis(ticker="SNGS")
        state = AsyncMock(spec=FSMContext)

        await cmd_analyze(mock_message, command, use_case, state)

        use_case.execute.assert_awaited_once_with("SNGS", Timeframe.D1)
        mock_message.answer.assert_awaited_once()
        state.clear.assert_awaited_once()

    async def test_use_case_exception_sends_friendly_error(
        self,
        mock_message: MagicMock,
    ) -> None:
        command = MagicMock(spec=CommandObject)
        command.args = "SNGS"
        use_case = AsyncMock(spec=AnalyzeInstrumentUseCase)
        use_case.execute.side_effect = KeyError("SNGS")
        state = AsyncMock(spec=FSMContext)

        await cmd_analyze(mock_message, command, use_case, state)

        mock_message.answer.assert_awaited_once()
        text = mock_message.answer.call_args[0][0]
        assert "Неизвестный тикер" in text or "⚠️" in text


# ---------------------------------------------------------------------------
# cb_start_analyze
# ---------------------------------------------------------------------------


class TestCbStartAnalyze:
    async def test_sets_state_and_shows_ticker_keyboard(self, mock_callback: MagicMock) -> None:
        state = AsyncMock(spec=FSMContext)

        await cb_start_analyze(mock_callback, state)

        state.set_state.assert_awaited_once_with(AnalyzeFlow.selecting_ticker)
        mock_callback.message.edit_text.assert_awaited_once()
        mock_callback.answer.assert_awaited_once()


# ---------------------------------------------------------------------------
# cb_ticker
# ---------------------------------------------------------------------------


class TestCbTicker:
    async def test_stores_ticker_and_shows_timeframe(self, mock_callback: MagicMock) -> None:
        callback_data = TickerCallback(ticker="SNGS")
        state = AsyncMock(spec=FSMContext)
        use_case = AsyncMock(spec=AnalyzeInstrumentUseCase)

        await cb_ticker(mock_callback, callback_data, state, use_case)

        state.update_data.assert_awaited_once_with(ticker="SNGS")
        state.set_state.assert_awaited_once_with(AnalyzeFlow.selecting_timeframe)
        mock_callback.message.edit_text.assert_awaited_once()
        mock_callback.answer.assert_awaited_once()


# ---------------------------------------------------------------------------
# cb_timeframe
# ---------------------------------------------------------------------------


class TestCbTimeframe:
    async def test_stores_tf_and_shows_type(self, mock_callback: MagicMock) -> None:
        callback_data = TimeframeCallback(value="1H")
        state = AsyncMock(spec=FSMContext)
        state.get_data.return_value = {"ticker": "SNGS"}

        await cb_timeframe(mock_callback, callback_data, state)

        state.update_data.assert_awaited_once_with(timeframe="1H")
        state.set_state.assert_awaited_once_with(AnalyzeFlow.selecting_type)
        mock_callback.message.edit_text.assert_awaited_once()
        mock_callback.answer.assert_awaited_once()

    async def test_invalid_timeframe_shows_alert(self, mock_callback: MagicMock) -> None:
        callback_data = TimeframeCallback(value="INVALID")
        state = AsyncMock(spec=FSMContext)

        await cb_timeframe(mock_callback, callback_data, state)

        mock_callback.answer.assert_awaited_once()


# ---------------------------------------------------------------------------
# cb_analysis_type
# ---------------------------------------------------------------------------


class TestCbAnalysisType:
    async def test_full_type_runs_analysis(self, mock_callback: MagicMock) -> None:
        callback_data = AnalyzeTypeCallback(type_="full")
        state = AsyncMock(spec=FSMContext)
        state.get_data.return_value = {"ticker": "SNGS", "timeframe": "1H"}
        use_case = AsyncMock(spec=AnalyzeInstrumentUseCase)
        use_case.execute.return_value = make_instrument_analysis(ticker="SNGS")

        await cb_analysis_type(mock_callback, callback_data, state, use_case)

        use_case.execute.assert_awaited_once_with("SNGS", Timeframe.H1)
        mock_callback.message.edit_text.assert_awaited_once()
        mock_callback.answer.assert_awaited_once()

    async def test_unknown_type_shows_alert(self, mock_callback: MagicMock) -> None:
        callback_data = AnalyzeTypeCallback(type_="unknown")
        state = AsyncMock(spec=FSMContext)
        use_case = AsyncMock(spec=AnalyzeInstrumentUseCase)

        await cb_analysis_type(mock_callback, callback_data, state, use_case)

        use_case.execute.assert_not_awaited()
        mock_callback.answer.assert_awaited_once()


# ---------------------------------------------------------------------------
# cb_analyze (legacy watchlist callback)
# ---------------------------------------------------------------------------


class TestCbAnalyze:
    async def test_calls_use_case_and_answers(self, mock_callback: MagicMock) -> None:
        callback_data = AnalyzeCallback(ticker="SNGS")
        use_case = AsyncMock(spec=AnalyzeInstrumentUseCase)
        use_case.execute.return_value = make_instrument_analysis(ticker="SNGS")
        state = AsyncMock(spec=FSMContext)

        await cb_analyze(mock_callback, callback_data, use_case, state)

        use_case.execute.assert_awaited_once_with("SNGS", Timeframe.D1)
        mock_callback.message.edit_text.assert_awaited_once()
        mock_callback.answer.assert_awaited_once()
        state.clear.assert_awaited_once()

    async def test_use_case_exception_sends_friendly_error(self, mock_callback: MagicMock) -> None:
        callback_data = AnalyzeCallback(ticker="VTBR")
        use_case = AsyncMock(spec=AnalyzeInstrumentUseCase)
        use_case.execute.side_effect = KeyError("VTBR")
        state = AsyncMock(spec=FSMContext)

        await cb_analyze(mock_callback, callback_data, use_case, state)

        mock_callback.message.edit_text.assert_awaited_once()
        text = mock_callback.message.edit_text.call_args[0][0]
        assert "Неизвестный тикер" in text or "⚠️" in text
        mock_callback.answer.assert_awaited_once()


# ---------------------------------------------------------------------------
# Back / Main menu navigation
# ---------------------------------------------------------------------------


class TestCbBack:
    async def test_from_ticker_goes_to_main_menu(self, mock_callback: MagicMock) -> None:
        state = AsyncMock(spec=FSMContext)
        state.get_state.return_value = AnalyzeFlow.selecting_ticker.state

        await cb_back(mock_callback, state)

        state.clear.assert_awaited_once()
        mock_callback.message.edit_text.assert_awaited_once()
        mock_callback.answer.assert_awaited_once()

    async def test_from_timeframe_goes_to_ticker(self, mock_callback: MagicMock) -> None:
        state = AsyncMock(spec=FSMContext)
        state.get_state.return_value = AnalyzeFlow.selecting_timeframe.state

        await cb_back(mock_callback, state)

        state.set_state.assert_awaited_once_with(AnalyzeFlow.selecting_ticker)
        mock_callback.message.edit_text.assert_awaited_once()
        mock_callback.answer.assert_awaited_once()

    async def test_from_type_goes_to_timeframe(self, mock_callback: MagicMock) -> None:
        state = AsyncMock(spec=FSMContext)
        state.get_state.return_value = AnalyzeFlow.selecting_type.state
        state.get_data.return_value = {"ticker": "SNGS"}

        await cb_back(mock_callback, state)

        state.set_state.assert_awaited_once_with(AnalyzeFlow.selecting_timeframe)
        mock_callback.message.edit_text.assert_awaited_once()
        mock_callback.answer.assert_awaited_once()

    async def test_unknown_state_goes_to_main_menu(self, mock_callback: MagicMock) -> None:
        state = AsyncMock(spec=FSMContext)
        state.get_state.return_value = None

        await cb_back(mock_callback, state)

        state.clear.assert_awaited_once()
        mock_callback.message.edit_text.assert_awaited_once()
        mock_callback.answer.assert_awaited_once()


class TestCbMainMenu:
    async def test_clears_state_and_shows_main_menu(self, mock_callback: MagicMock) -> None:
        state = AsyncMock(spec=FSMContext)

        await cb_main_menu(mock_callback, state)

        state.clear.assert_awaited_once()
        mock_callback.message.edit_text.assert_awaited_once()
        mock_callback.answer.assert_awaited_once()


# ---------------------------------------------------------------------------
# Refresh (🔄 Обновить данные) — must edit the existing message, not resend
# ---------------------------------------------------------------------------


class TestCbRefreshAnalysis:
    async def test_refresh_updates_existing_message(self, mock_callback: MagicMock) -> None:
        callback_data = RefreshCallback(ticker="SNGS", tf_value="1D")
        use_case = AsyncMock(spec=AnalyzeInstrumentUseCase)
        use_case.execute.return_value = make_instrument_analysis(ticker="SNGS")

        await cb_refresh_analysis(mock_callback, callback_data, use_case)

        use_case.execute.assert_awaited_once_with("SNGS", Timeframe.D1)
        mock_callback.message.edit_text.assert_awaited_once()
        mock_callback.answer.assert_awaited_once()

    async def test_refresh_creates_no_duplicate_message(self, mock_callback: MagicMock) -> None:
        callback_data = RefreshCallback(ticker="SNGS", tf_value="1D")
        use_case = AsyncMock(spec=AnalyzeInstrumentUseCase)
        use_case.execute.return_value = make_instrument_analysis(ticker="SNGS")

        await cb_refresh_analysis(mock_callback, callback_data, use_case)

        # The message is edited in place — no fresh message is ever sent.
        mock_callback.message.answer.assert_not_awaited()

    async def test_refresh_unchanged_content_does_not_resend(
        self, mock_callback: MagicMock
    ) -> None:
        # Identical data → Telegram reports "message is not modified"; we must
        # treat that as success and NOT send a new message.
        callback_data = RefreshCallback(ticker="SNGS", tf_value="1D")
        use_case = AsyncMock(spec=AnalyzeInstrumentUseCase)
        use_case.execute.return_value = make_instrument_analysis(ticker="SNGS")
        mock_callback.message.edit_text.side_effect = _bad_request(
            "Bad Request: message is not modified"
        )

        await cb_refresh_analysis(mock_callback, callback_data, use_case)

        mock_callback.message.answer.assert_not_awaited()
        mock_callback.answer.assert_awaited_once()

    async def test_refresh_does_not_create_new_message_on_edit_failure(
        self, mock_callback: MagicMock
    ) -> None:
        """edit_or_answer must NOT fall back to a new message on edit failure."""
        callback_data = RefreshCallback(ticker="SNGS", tf_value="1D")
        use_case = AsyncMock(spec=AnalyzeInstrumentUseCase)
        use_case.execute.return_value = make_instrument_analysis(ticker="SNGS")
        mock_callback.message.edit_text.side_effect = _bad_request(
            "Bad Request: message can't be edited"
        )

        await cb_refresh_analysis(mock_callback, callback_data, use_case)

        mock_callback.message.answer.assert_not_awaited()


# ---------------------------------------------------------------------------
# _edit_or_answer
# ---------------------------------------------------------------------------


class TestEditOrAnswer:
    async def test_edits_in_place(self, mock_message: MagicMock) -> None:
        mock_message.edit_text = AsyncMock()

        await _edit_or_answer(mock_message, "hello")

        mock_message.edit_text.assert_awaited_once()
        mock_message.answer.assert_not_awaited()

    async def test_not_modified_is_swallowed(self, mock_message: MagicMock) -> None:
        mock_message.edit_text = AsyncMock(
            side_effect=_bad_request("Bad Request: message is not modified")
        )

        await _edit_or_answer(mock_message, "hello")

        mock_message.answer.assert_not_awaited()

    async def test_real_failure_does_not_create_new_message(self, mock_message: MagicMock) -> None:
        mock_message.edit_text = AsyncMock(
            side_effect=_bad_request("Bad Request: message to edit not found")
        )

        await _edit_or_answer(mock_message, "hello")

        mock_message.answer.assert_not_awaited()


# ---------------------------------------------------------------------------
# Custom ticker
# ---------------------------------------------------------------------------


class TestCbCustomTicker:
    async def test_sets_state_and_prompts(self, mock_callback: MagicMock) -> None:
        state = AsyncMock(spec=FSMContext)

        await cb_custom_ticker(mock_callback, state)

        state.set_state.assert_awaited_once_with(AnalyzeFlow.custom_ticker)
        mock_callback.message.edit_text.assert_awaited_once()
        mock_callback.answer.assert_awaited_once()


class TestMsgCustomTicker:
    async def test_valid_ticker_proceeds_to_timeframe(self, mock_message: MagicMock) -> None:
        mock_message.text = "SNGS"
        state = AsyncMock(spec=FSMContext)
        use_case = AsyncMock(spec=AnalyzeInstrumentUseCase)
        use_case.execute.return_value = make_instrument_analysis(ticker="SNGS")

        await msg_custom_ticker(mock_message, state, use_case)

        state.update_data.assert_awaited_once_with(ticker="SNGS")
        state.set_state.assert_awaited_once_with(AnalyzeFlow.selecting_timeframe)
        mock_message.answer.assert_awaited_once()

    async def test_invalid_ticker_shows_error(self, mock_message: MagicMock) -> None:
        mock_message.text = "INVALID"
        state = AsyncMock(spec=FSMContext)
        use_case = AsyncMock(spec=AnalyzeInstrumentUseCase)

        await msg_custom_ticker(mock_message, state, use_case)

        text = mock_message.answer.call_args[0][0]
        assert "не найден" in text
        state.set_state.assert_awaited_once_with(AnalyzeFlow.selecting_ticker)

    async def test_empty_text_shows_prompt(self, mock_message: MagicMock) -> None:
        mock_message.text = ""
        state = AsyncMock(spec=FSMContext)
        use_case = AsyncMock(spec=AnalyzeInstrumentUseCase)

        await msg_custom_ticker(mock_message, state, use_case)

        mock_message.answer.assert_awaited_once()
