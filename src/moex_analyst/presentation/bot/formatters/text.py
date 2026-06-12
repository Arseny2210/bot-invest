"""Low-level text helpers shared by the message formatters.

Everything here is pure and free of aiogram/domain side effects: value →
string. Output targets Telegram **HTML** parse mode, so all interpolated
dynamic text is HTML-escaped at the point it enters a message.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from html import escape as _html_escape

from moex_analyst.domain.alerts.enums import AlertDirection, AlertSeverity
from moex_analyst.domain.analysis.enums import (
    StructurePoint,
    TrendDirection,
    TrendStrength,
    VolumeCondition,
)
from moex_analyst.domain.market.timeframe import Timeframe
from moex_analyst.infrastructure.moex.config import INSTRUMENT_REGISTRY

__all__ = [
    "S",
    "alert_direction_icon",
    "alert_severity_icon",
    "escape",
    "fmt_aligned",
    "fmt_datetime",
    "fmt_datetime_msk",
    "fmt_decimal",
    "fmt_freshness_block",
    "fmt_instrument_menu",
    "fmt_instrument_name",
    "fmt_percent",
    "fmt_score",
    "freshness_indicator",
    "is_stale",
    "section_divider",
    "structure_point_label",
    "trend_direction_label",
    "trend_icon",
    "trend_strength_label",
    "volume_label",
]

_EM_DASH = "—"
_SECTION_DIVIDER = "━" * 24

# Moscow time is a fixed UTC+3 offset (Russia observes no DST). MOEX trades and
# reports in MSK, so all user-facing timestamps are rendered in this zone.
_MSK = timezone(timedelta(hours=3))
_DATA_SOURCE = "MOEX ISS"


def S(bold: str, rest: str = "") -> str:
    """Return a two-column line: bold label + value."""
    if rest:
        return f"<b>{bold}</b> {rest}"
    return f"<b>{bold}</b>"


def section_divider() -> str:
    return _SECTION_DIVIDER


def fmt_instrument_name(ticker: str) -> str:
    """Return human-friendly instrument label: ``Name (TICKER)``.

    Falls back to bare ``ticker`` for instruments not in the registry (e.g.
    user-provided custom tickers).
    """
    ref = INSTRUMENT_REGISTRY.get(ticker)
    if ref is None or not ref.display_name_ru:
        return ticker
    return f"{ref.display_name_ru} ({ref.ticker})"


def fmt_instrument_menu(ticker: str) -> str:
    """Like :func:`fmt_instrument_name` but includes the icon for menus.

    Returns ``icon Name (TICKER)`` or bare ``ticker`` as fallback.
    """
    ref = INSTRUMENT_REGISTRY.get(ticker)
    if ref is None or not ref.display_name_ru:
        return ticker
    icon = ref.icon or "📌"
    return f"{icon} {ref.display_name_ru} ({ref.ticker})"


def fmt_aligned(value: str, width: int = 18) -> str:
    """Pad a value with non-breaking spaces to a minimum width."""
    needed = max(0, width - len(value))
    return value + "\u00a0" * needed


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
    AlertSeverity.INFO: "ℹ️",
    AlertSeverity.WARNING: "⚠️",
    AlertSeverity.CRITICAL: "🚨",
}

_TREND_DIRECTION_LABELS: dict[TrendDirection, str] = {
    TrendDirection.UP: "восходящий",
    TrendDirection.DOWN: "нисходящий",
    TrendDirection.SIDEWAYS: "боковик",
}

_TREND_STRENGTH_LABELS: dict[TrendStrength, str] = {
    TrendStrength.STRONG: "сильный",
    TrendStrength.WEAK: "слабый",
    TrendStrength.NONE: "—",
}

_STRUCTURE_POINT_LABELS: dict[StructurePoint, str] = {
    StructurePoint.HH: "ВВ",
    StructurePoint.HL: "ВН",
    StructurePoint.LH: "НВ",
    StructurePoint.LL: "НН",
}

_VOLUME_LABELS: dict[VolumeCondition, str] = {
    VolumeCondition.HIGH: "🔊 высокий",
    VolumeCondition.NORMAL: "🔈 нормальный",
    VolumeCondition.LOW: "🔉 низкий",
    VolumeCondition.UNKNOWN: "— н/д",
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
    """Format a timezone-aware instant as ``DD.MM.YYYY HH:MM`` (no conversion)."""
    return value.strftime("%d.%m.%Y %H:%M")


def fmt_datetime_msk(value: datetime) -> str:
    """Render a tz-aware instant in Moscow time as ``DD.MM.YYYY HH:MM МСК``.

    Naive datetimes are assumed to already be UTC before conversion.
    """
    aware = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    return aware.astimezone(_MSK).strftime("%d.%m.%Y %H:%M") + " МСК"


def trend_icon(direction: TrendDirection) -> str:
    return _TREND_ICONS[direction]


def alert_direction_icon(direction: AlertDirection) -> str:
    return _DIRECTION_ICONS[direction]


def alert_severity_icon(severity: AlertSeverity) -> str:
    return _SEVERITY_ICONS[severity]


def volume_label(condition: VolumeCondition) -> str:
    return _VOLUME_LABELS[condition]


def trend_direction_label(direction: TrendDirection) -> str:
    return _TREND_DIRECTION_LABELS[direction]


def trend_strength_label(strength: TrendStrength) -> str:
    return _TREND_STRENGTH_LABELS[strength]


def structure_point_label(point: StructurePoint) -> str:
    return _STRUCTURE_POINT_LABELS[point]


_STALE_THRESHOLDS: dict[Timeframe, timedelta] = {
    Timeframe.M15: timedelta(minutes=20),
    Timeframe.H1: timedelta(minutes=90),
    Timeframe.H4: timedelta(hours=5),
    Timeframe.D1: timedelta(days=1),
    Timeframe.W1: timedelta(days=7),
}


def is_stale(as_of: datetime, timeframe: Timeframe) -> bool:
    threshold = _STALE_THRESHOLDS.get(timeframe, timedelta(days=1))
    return datetime.now(UTC) - as_of > threshold


def freshness_indicator(as_of: datetime, timeframe: Timeframe) -> str:
    return "🟢" if not is_stale(as_of, timeframe) else "🟡"


def fmt_freshness_block(as_of: datetime, timeframe: Timeframe) -> str:
    """Render the multi-line freshness footer shown on every data screen.

    Always states *when* the analysis was generated (in MSK), the data source,
    and whether the data is current. When the data has exceeded the timeframe's
    staleness threshold it switches the indicator to "needs refresh" and adds an
    explicit warning, so the bot never presents stale data as current.
    """
    stale = is_stale(as_of, timeframe)
    indicator = "🟡 Требуется обновление" if stale else "🟢 Актуальные данные"
    lines = [
        "🕒 Последнее обновление:",
        fmt_datetime_msk(as_of),
        f"📡 Источник: {_DATA_SOURCE}",
        indicator,
    ]
    if stale:
        lines.append("⚠️ Данные могли устареть.")
    return "\n".join(lines)
