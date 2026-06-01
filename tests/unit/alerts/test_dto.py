"""Unit tests for the alert DTOs (Alert, AlertReport) and the severity ordering."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from moex_analyst.domain.alerts.dto import Alert, AlertReport
from moex_analyst.domain.alerts.enums import AlertDirection, AlertSeverity, AlertType
from moex_analyst.domain.market.timeframe import Timeframe

_AS_OF = datetime(2024, 6, 1, 12, tzinfo=UTC)


def _alert(
    *,
    type_: AlertType = AlertType.RSI_OVERBOUGHT,
    direction: AlertDirection = AlertDirection.BEARISH,
    severity: AlertSeverity = AlertSeverity.WARNING,
    score: float = 0.5,
    ticker: str = "SBER",
    timeframe: Timeframe = Timeframe.H1,
) -> Alert:
    return Alert(
        type=type_,
        direction=direction,
        severity=severity,
        score=score,
        message="msg",
        ticker=ticker,
        timeframe=timeframe,
        as_of=_AS_OF,
    )


class TestAlert:
    def test_dedup_key_is_stable_and_descriptive(self) -> None:
        alert = _alert()
        assert alert.dedup_key == "SBER:1H:rsi_overbought:bearish"

    def test_dedup_key_differs_by_direction(self) -> None:
        a = _alert(direction=AlertDirection.BULLISH)
        b = _alert(direction=AlertDirection.BEARISH)
        assert a.dedup_key != b.dedup_key

    def test_is_frozen(self) -> None:
        alert = _alert()
        with pytest.raises(ValidationError):
            alert.score = 0.9  # type: ignore[misc]

    def test_score_must_be_in_unit_interval(self) -> None:
        with pytest.raises(ValidationError):
            _alert(score=1.5)

    def test_message_must_be_non_empty(self) -> None:
        with pytest.raises(ValidationError):
            Alert(
                type=AlertType.VOLUME_SPIKE,
                direction=AlertDirection.NEUTRAL,
                severity=AlertSeverity.INFO,
                score=0.1,
                message="",
                ticker="SBER",
                timeframe=Timeframe.H1,
                as_of=_AS_OF,
            )

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            Alert(
                type=AlertType.VOLUME_SPIKE,
                direction=AlertDirection.NEUTRAL,
                severity=AlertSeverity.INFO,
                score=0.1,
                message="m",
                ticker="SBER",
                timeframe=Timeframe.H1,
                as_of=_AS_OF,
                bogus=1,  # type: ignore[call-arg]
            )


class TestSeverityRank:
    def test_rank_is_monotonic(self) -> None:
        assert (
            AlertSeverity.INFO.rank
            < AlertSeverity.WARNING.rank
            < AlertSeverity.CRITICAL.rank
        )


class TestAlertReport:
    def test_empty_report(self) -> None:
        report = AlertReport(
            ticker="SBER", timeframe=Timeframe.H1, as_of=_AS_OF, alerts=(),
        )
        assert report.is_empty
        assert report.highest_severity is None

    def test_highest_severity_picks_strongest(self) -> None:
        report = AlertReport(
            ticker="SBER",
            timeframe=Timeframe.H1,
            as_of=_AS_OF,
            alerts=(
                _alert(severity=AlertSeverity.INFO),
                _alert(severity=AlertSeverity.CRITICAL),
                _alert(severity=AlertSeverity.WARNING),
            ),
        )
        assert not report.is_empty
        assert report.highest_severity is AlertSeverity.CRITICAL
