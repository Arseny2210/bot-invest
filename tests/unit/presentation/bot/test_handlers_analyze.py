from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.filters import CommandObject

from moex_analyst.application.use_cases import AnalyzeInstrumentUseCase
from moex_analyst.domain.market.timeframe import Timeframe
from moex_analyst.presentation.bot.callbacks import AnalyzeCallback
from moex_analyst.presentation.bot.handlers.analyze import (
    _parse_args,
    cb_analyze,
    cmd_analyze,
)
from tests.unit.presentation.bot.formatters.conftest import make_instrument_analysis


class TestParseArgs:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            (None, None),
            ("", None),
            ("   ", None),
            ("SNGS", ("SNGS", Timeframe.D1)),
            ("sngs", ("SNGS", Timeframe.D1)),
            ("SNGS 1H", ("SNGS", Timeframe.H1)),
            ("SNGS H1", ("SNGS", Timeframe.H1)),
            ("SNGS 4H", ("SNGS", Timeframe.H4)),
            ("SNGS H4", ("SNGS", Timeframe.H4)),
            ("SNGS 1D", ("SNGS", Timeframe.D1)),
            ("SNGS D1", ("SNGS", Timeframe.D1)),
            ("SNGS DAY", ("SNGS", Timeframe.D1)),
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


class TestCmdAnalyze:
    async def test_no_args_sends_error(
        self, mock_message: MagicMock, mock_command: MagicMock
    ) -> None:
        mock_command.args = None
        use_case = AsyncMock(spec=AnalyzeInstrumentUseCase)

        await cmd_analyze(mock_message, mock_command, use_case)

        mock_message.answer.assert_awaited_once()
        text = mock_message.answer.call_args[0][0]
        assert "Usage" in text
        use_case.execute.assert_not_awaited()

    async def test_valid_args_calls_use_case(self, mock_message: MagicMock) -> None:
        command = MagicMock(spec=CommandObject)
        command.args = "SNGS"
        use_case = AsyncMock(spec=AnalyzeInstrumentUseCase)
        use_case.execute.return_value = make_instrument_analysis(ticker="SNGS")

        await cmd_analyze(mock_message, command, use_case)

        use_case.execute.assert_awaited_once_with("SNGS", Timeframe.D1)
        mock_message.answer.assert_awaited_once()

    async def test_use_case_exception_sends_friendly_error(
        self,
        mock_message: MagicMock,
    ) -> None:
        command = MagicMock(spec=CommandObject)
        command.args = "SNGS"
        use_case = AsyncMock(spec=AnalyzeInstrumentUseCase)
        use_case.execute.side_effect = KeyError("SNGS")

        await cmd_analyze(mock_message, command, use_case)

        mock_message.answer.assert_awaited_once()
        text = mock_message.answer.call_args[0][0]
        assert "Unknown ticker" in text or "⚠️" in text


class TestCbAnalyze:
    async def test_calls_use_case_and_answers(self, mock_callback: MagicMock) -> None:
        callback_data = AnalyzeCallback(ticker="SNGS")
        use_case = AsyncMock(spec=AnalyzeInstrumentUseCase)
        use_case.execute.return_value = make_instrument_analysis(ticker="SNGS")

        await cb_analyze(mock_callback, callback_data, use_case)

        use_case.execute.assert_awaited_once_with("SNGS", Timeframe.D1)
        mock_callback.message.answer.assert_awaited_once()
        mock_callback.answer.assert_awaited_once()

    async def test_use_case_exception_sends_friendly_error(self, mock_callback: MagicMock) -> None:
        callback_data = AnalyzeCallback(ticker="VTBR")
        use_case = AsyncMock(spec=AnalyzeInstrumentUseCase)
        use_case.execute.side_effect = KeyError("VTBR")

        await cb_analyze(mock_callback, callback_data, use_case)

        mock_callback.message.answer.assert_awaited_once()
        text = mock_callback.message.answer.call_args[0][0]
        assert "Unknown ticker" in text or "⚠️" in text
        mock_callback.answer.assert_awaited_once()
