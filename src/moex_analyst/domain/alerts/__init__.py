"""Deterministic alert engine.

Pure-Python, no I/O, no AI, no Telegram, no database. Consumes one
:class:`AnalysisResult` and produces a list of :class:`Alert` objects covering
support/resistance breaks, trend and market-structure changes, EMA alignment,
RSI extremes, volume spikes and composite strong-signal confluences.

Given the same :class:`AnalysisResult`, the detector always returns the same
ordered alerts (deterministic and idempotent). Edge-triggering and delivery are
the caller's concern, keyed off :attr:`Alert.dedup_key`.
"""

from __future__ import annotations

from moex_analyst.domain.alerts.detector import AlertDetector
from moex_analyst.domain.alerts.dto import Alert, AlertReport
from moex_analyst.domain.alerts.enums import AlertDirection, AlertSeverity, AlertType
from moex_analyst.domain.alerts.rules import DEFAULT_RULES, Rule

__all__ = [
    "DEFAULT_RULES",
    "Alert",
    "AlertDetector",
    "AlertDirection",
    "AlertReport",
    "AlertSeverity",
    "AlertType",
    "Rule",
]
