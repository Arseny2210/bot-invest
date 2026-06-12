"""ORM models — one per database table.

Importing this module registers every model on ``Base.metadata``, which is
required for Alembic autogenerate to see the full schema.
"""

from __future__ import annotations

from moex_analyst.infrastructure.db.models.alert_record import AlertRecord
from moex_analyst.infrastructure.db.models.analysis_record import AnalysisRecord
from moex_analyst.infrastructure.db.models.forecast_record import (
    ForecastOutcome,
    ForecastRecord,
    ForecastStatus,
)

__all__ = [
    "AlertRecord",
    "AnalysisRecord",
    "ForecastOutcome",
    "ForecastRecord",
    "ForecastStatus",
]
