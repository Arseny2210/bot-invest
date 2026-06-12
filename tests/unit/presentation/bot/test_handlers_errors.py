import pytest

from moex_analyst.application.exceptions import (
    DataSourceError,
    EmptyDataError,
    InstrumentNotFoundError,
    RateLimitError,
    TickerNotFoundError,
)
from moex_analyst.domain.analysis import InsufficientDataError
from moex_analyst.presentation.bot.handlers.errors import friendly_error


class TestFriendlyError:
    @pytest.mark.parametrize(
        ("exc", "expected_substring"),
        [
            (TickerNotFoundError("UNKNOWN"), "Тикер не найден"),
            (InsufficientDataError(required=50, got=10), "Недостаточно истории цен"),
            (InstrumentNotFoundError("SNGS"), "нет данных"),
            (EmptyDataError("SNGS"), "не вернул данных"),
            (RateLimitError("SNGS"), "ограничивает запросы"),
            (DataSourceError("connection failed"), "Не удалось подключиться"),
            (Exception("anything"), "Что-то пошло не так"),
            (ValueError("bad value"), "Что-то пошло не так"),
        ],
    )
    def test_maps_to_expected_message(
        self,
        exc: Exception,
        expected_substring: str,
    ) -> None:
        result = friendly_error(exc)
        assert expected_substring in result
        assert "⚠️" in result

    def test_ticker_not_found_suggests_menu(self) -> None:
        result = friendly_error(TickerNotFoundError("NONEXISTENT"))
        assert "меню" in result

    def test_error_is_html_formatted(self) -> None:
        result = friendly_error(ValueError("test"))
        assert result.startswith("⚠️")
