"""Unit tests for the statistics formatter — format_statistics."""

from __future__ import annotations

from moex_analyst.application.services.dto import ForecastMetrics
from moex_analyst.presentation.bot.formatters.statistics import format_statistics


class TestFormatStatistics:
    def test_no_metrics(self) -> None:
        text = format_statistics(None)
        assert "нет завершённых прогнозов" in text
        assert "ТОЧНОСТЬ ПРОГНОЗОВ" in text

    def test_zero_predictions(self) -> None:
        metrics = ForecastMetrics(
            total_predictions=0,
            successful_predictions=0,
            failed_predictions=0,
            success_rate=0.0,
            average_price_change=0.0,
        )
        text = format_statistics(metrics)
        assert "нет завершённых прогнозов" in text

    def test_all_successful(self) -> None:
        metrics = ForecastMetrics(
            total_predictions=10,
            successful_predictions=10,
            failed_predictions=0,
            success_rate=1.0,
            average_price_change=2.5,
        )
        text = format_statistics(metrics)
        assert "10" in text
        assert "100.0%" in text  # success_pct
        assert "0.0%" in text  # fail_pct
        assert "+2.50%" in text
        assert "В ожидании" not in text

    def test_all_failed(self) -> None:
        metrics = ForecastMetrics(
            total_predictions=5,
            successful_predictions=0,
            failed_predictions=5,
            success_rate=0.0,
            average_price_change=-3.2,
        )
        text = format_statistics(metrics)
        assert "5" in text
        assert "0.0%" in text  # success_pct
        assert "100.0%" in text  # fail_pct
        assert "-3.20%" in text

    def test_mixed_with_pending(self) -> None:
        """Pending forecasts must NOT be counted as failed."""
        metrics = ForecastMetrics(
            total_predictions=20,
            successful_predictions=8,
            failed_predictions=4,
            success_rate=0.4,
            average_price_change=1.0,
        )
        text = format_statistics(metrics)
        assert "20" in text
        assert "8" in text
        assert "40.0%" in text  # success_pct (8/20)
        assert "4" in text
        assert "20.0%" in text  # fail_pct (4/20), NOT 60.0%
        assert "20.0%" in text  # success rate 40% should NOT make fail 60%
        assert "8" in text  # pending = 20 - 8 - 4 = 8
        assert "В ожидании" in text

    def test_negative_average_change_shows_minus(self) -> None:
        metrics = ForecastMetrics(
            total_predictions=3,
            successful_predictions=1,
            failed_predictions=2,
            success_rate=1.0 / 3.0,
            average_price_change=-5.0,
        )
        text = format_statistics(metrics)
        assert "-5.00%" in text
        assert "+" not in text

    def test_zero_average_change_shows_plus(self) -> None:
        metrics = ForecastMetrics(
            total_predictions=1,
            successful_predictions=1,
            failed_predictions=0,
            success_rate=1.0,
            average_price_change=0.0,
        )
        text = format_statistics(metrics)
        assert "+0.00%" in text

    def test_success_rate_rounding(self) -> None:
        """2/3 ≈ 66.7% success, 1/3 ≈ 33.3% fail, 0 pending."""
        metrics = ForecastMetrics(
            total_predictions=3,
            successful_predictions=2,
            failed_predictions=1,
            success_rate=2.0 / 3.0,
            average_price_change=0.5,
        )
        text = format_statistics(metrics)
        assert "66.7%" in text
        assert "33.3%" in text
