"""Application-layer DTOs for the forecasting subsystem."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["ForecastMetrics"]


@dataclass(frozen=True, slots=True)
class ForecastMetrics:
    """Aggregate forecast accuracy statistics."""

    total_predictions: int
    successful_predictions: int
    failed_predictions: int
    success_rate: float
    average_price_change: float
