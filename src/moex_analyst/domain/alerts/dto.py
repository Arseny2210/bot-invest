"""Output contract of the alert engine: :class:`Alert` and :class:`AlertReport`.

Immutable Pydantic models, mirroring the analysis-layer DTOs. An :class:`Alert`
is a single deterministic verdict derived from one :class:`AnalysisResult`; an
:class:`AlertReport` bundles the alerts raised for one instrument + timeframe
together with the analysis timestamp they were computed from.

These models carry no behaviour beyond a stable :attr:`Alert.dedup_key`. The
*engine* is pure: edge-triggering (suppressing an alert that already fired on a
previous snapshot) belongs to the caller, which keys off ``dedup_key`` — there
is no state, Telegram or database dependency here.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from moex_analyst.domain.alerts.enums import AlertDirection, AlertSeverity, AlertType
from moex_analyst.domain.market.timeframe import Timeframe

__all__ = [
    "Alert",
    "AlertReport",
]


class _FrozenModel(BaseModel):
    """Base for immutable alert DTOs."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class Alert(_FrozenModel):
    """A single deterministic alert raised from an analysis snapshot."""

    type: AlertType
    direction: AlertDirection
    severity: AlertSeverity
    # Confidence/intensity of the signal in [0, 1].
    score: float = Field(ge=0.0, le=1.0)
    # Human-readable, deterministic summary (no locale/time-dependent content).
    message: str = Field(min_length=1)

    # Provenance — copied from the source AnalysisResult for traceability.
    ticker: str
    timeframe: Timeframe
    as_of: datetime

    @property
    def dedup_key(self) -> str:
        """Stable identity for edge-triggering by a stateful caller.

        Two alerts of the same type and direction for the same instrument +
        timeframe share a key, so a caller can suppress re-firing across
        snapshots without the engine holding any state itself.
        """
        return f"{self.ticker}:{self.timeframe.value}:{self.type.value}:{self.direction.value}"


class AlertReport(_FrozenModel):
    """All alerts raised for one instrument + timeframe from a single analysis."""

    ticker: str
    timeframe: Timeframe
    as_of: datetime
    alerts: tuple[Alert, ...]

    @property
    def is_empty(self) -> bool:
        return not self.alerts

    @property
    def highest_severity(self) -> AlertSeverity | None:
        """Severity of the strongest alert, or ``None`` when there are none."""
        if not self.alerts:
            return None
        return max((a.severity for a in self.alerts), key=lambda s: s.rank)
