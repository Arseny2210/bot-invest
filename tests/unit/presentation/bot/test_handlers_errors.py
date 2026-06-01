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
            (TickerNotFoundError("UNKNOWN"), "Unknown ticker"),
            (InsufficientDataError(required=50, got=10), "Not enough price history"),
            (InstrumentNotFoundError("SNGS"), "MOEX has no data"),
            (EmptyDataError("SNGS"), "MOEX returned no data"),
            (RateLimitError("SNGS"), "rate-limiting"),
            (DataSourceError("connection failed"), "Couldn't reach MOEX"),
            (Exception("anything"), "Something went wrong"),
            (ValueError("bad value"), "Something went wrong"),
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

    def test_ticker_not_found_mentions_tracked_instruments(self) -> None:
        result = friendly_error(TickerNotFoundError("NONEXISTENT"))
        assert "Tracked instruments" in result

    def test_error_is_html_formatted(self) -> None:
        result = friendly_error(ValueError("test"))
        assert result.startswith("⚠️")
