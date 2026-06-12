"""Repository implementations — one per aggregate / table.

Each repository extends :class:`BaseRepository` and provides domain-specific
query methods.  Repositories never open transactions or commit — that is the
Unit of Work's responsibility.
"""

from __future__ import annotations

from moex_analyst.infrastructure.db.repositories.alert_repository import AlertRepository
from moex_analyst.infrastructure.db.repositories.analysis_repository import (
    AnalysisRepository,
)
from moex_analyst.infrastructure.db.repositories.base import BaseRepository
from moex_analyst.infrastructure.db.repositories.forecast_repository import (
    ForecastOutcomeRepository,
    ForecastRepository,
)

__all__ = [
    "AlertRepository",
    "AnalysisRepository",
    "BaseRepository",
    "ForecastOutcomeRepository",
    "ForecastRepository",
]
