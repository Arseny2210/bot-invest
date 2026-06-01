"""Alert detector: turns one :class:`AnalysisResult` into a list of alerts.

The detector is a thin, stateless orchestrator over the pure rule functions in
:mod:`moex_analyst.domain.alerts.rules`. It runs each rule once, in a fixed
order, and collects the alerts that fire. Because every rule is pure and the
order is fixed, the detector is itself deterministic and idempotent: the same
:class:`AnalysisResult` always yields the same ordered list of alerts.

No I/O, no Telegram, no database — emitting/persisting alerts is the caller's
concern (see :attr:`Alert.dedup_key`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from moex_analyst.domain.alerts.dto import Alert, AlertReport
from moex_analyst.domain.alerts.rules import DEFAULT_RULES

if TYPE_CHECKING:
    from collections.abc import Sequence

    from moex_analyst.domain.alerts.rules import Rule
    from moex_analyst.domain.analysis.result import AnalysisResult

__all__ = ["AlertDetector"]


class AlertDetector:
    """Evaluates a fixed set of rules against an analysis snapshot.

    Stateless and reusable across instruments and timeframes. Construct once and
    call :meth:`detect` (or :meth:`detect_report`) per :class:`AnalysisResult`.
    A custom ``rules`` sequence can be injected for testing or for a reduced
    alert set; it defaults to :data:`DEFAULT_RULES` in canonical order.
    """

    def __init__(self, rules: Sequence[Rule] | None = None) -> None:
        self._rules: tuple[Rule, ...] = (
            tuple(rules) if rules is not None else DEFAULT_RULES
        )

    def detect(self, result: AnalysisResult) -> list[Alert]:
        """Return every alert raised by the configured rules, in rule order."""
        alerts: list[Alert] = []
        for rule in self._rules:
            alert = rule(result)
            if alert is not None:
                alerts.append(alert)
        return alerts

    def detect_report(self, result: AnalysisResult) -> AlertReport:
        """Wrap :meth:`detect` output in an :class:`AlertReport` with provenance."""
        return AlertReport(
            ticker=result.ticker,
            timeframe=result.timeframe,
            as_of=result.as_of,
            alerts=tuple(self.detect(result)),
        )
