"""Low-level text helpers shared by the message formatters.

Everything here is pure and free of aiogram/domain side effects: value →
string. Output targets Telegram **HTML** parse mode, so all interpolated
dynamic text is HTML-escaped at the point it enters a message.
"""

from __future__ import annotations

from decimal import Decimal
from html import escape as _html_escape
from typing import TYPE_CHECKING

from moex_analyst.domain.alerts.enums import AlertDirection, AlertSeverity
from moex_analyst.domain.analysis.enums import TrendDirection, VolumeCondition

if TYPE_CHECKING:
    from datetime import datetime

__all__ = [
    "alert_direction_icon",
    "alert_severity_icon",
    "escape",
    "fmt_datetime",
    "fmt_decimal",
    "fmt_percent",
    "fmt_score",
    "trend_icon",
    "volume_label",
]

_EM_DASH = "—"

_TREND_ICONS: dict[TrendDirection, str] = {
    TrendDirection.UP: "📈",
    TrendDirection.DOWN: "📉",
    TrendDirection.SIDEWAYS: "➡️",
}

_DIRECTION_ICONS: dict[AlertDirection, str] = {
    AlertDirection.BULLISH: "🟢",
    AlertDirection.BEARISH: "🔴",
    AlertDirection.NEUTRAL: "⚪",
}

_SEVERITY_ICONS: dict[AlertSeverity, str] = {
    AlertSeverity.INFO: "ℹ️",  # noqa: RUF001 - INFORMATION SOURCE emoji is intentional
    AlertSeverity.WARNING: "⚠️",
    AlertSeverity.CRITICAL: "🚨",
}

_VOLUME_LABELS: dict[VolumeCondition, str] = {
    VolumeCondition.HIGH: "🔊 high",
    VolumeCondition.NORMAL: "🔈 normal",
    VolumeCondition.LOW: "🔉 low",
    VolumeCondition.UNKNOWN: "— n/a",
}


def escape(value: str) -> str:
    """HTML-escape user/dynamic text for safe inclusion in an HTML message."""
    return _html_escape(value, quote=False)


def fmt_decimal(value: Decimal | None, *, places: int = 2) -> str:
    """Format an optional ``Decimal`` to fixed places, or an em dash if absent."""
    if value is None:
        return _EM_DASH
    quant = Decimal(1).scaleb(-places)
    return f"{value.quantize(quant):,}"


def fmt_percent(value: float, *, places: int = 1) -> str:
    """Format a ``[0, 1]`` probability as a percentage string."""
    return f"{value * 100:.{places}f}%"


def fmt_score(value: float, *, places: int = 2) -> str:
    """Format a signed ``[-1, 1]`` score with an explicit sign."""
    return f"{value:+.{places}f}"


def fmt_datetime(value: datetime) -> str:
    """Format a timezone-aware instant as ``YYYY-MM-DD HH:MM UTC``."""
    return value.strftime("%Y-%m-%d %H:%M UTC")


def trend_icon(direction: TrendDirection) -> str:
    return _TREND_ICONS[direction]


def alert_direction_icon(direction: AlertDirection) -> str:
    return _DIRECTION_ICONS[direction]


def alert_severity_icon(severity: AlertSeverity) -> str:
    return _SEVERITY_ICONS[severity]


def volume_label(condition: VolumeCondition) -> str:
    return _VOLUME_LABELS[condition]
