from __future__ import annotations

from typing import TYPE_CHECKING

from moex_analyst.presentation.bot.formatters.text import fmt_percent, section_divider

if TYPE_CHECKING:
    from moex_analyst.application.services.dto import ForecastMetrics

__all__ = ["format_statistics"]


def format_statistics(metrics: ForecastMetrics | None) -> str:
    lines: list[str] = [
        section_divider(),
        "📊 <b>ТОЧНОСТЬ ПРОГНОЗОВ</b>",
        section_divider(),
        "",
    ]

    if metrics is None or metrics.total_predictions == 0:
        lines.append("📭 Пока нет завершённых прогнозов")
        lines.append("")
        lines.append(section_divider())
        return "\n".join(lines)

    success_pct = fmt_percent(metrics.success_rate, places=1)
    total = metrics.total_predictions
    fail_rate = metrics.failed_predictions / total if total > 0 else 0.0
    fail_pct = fmt_percent(fail_rate, places=1)
    pending = total - metrics.successful_predictions - metrics.failed_predictions
    change_sign = "+" if metrics.average_price_change >= 0 else ""

    lines.extend(
        [
            f"📊 Всего прогнозов:      <b>{total}</b>",
            "",
            f"✅ Успешных:             <b>{metrics.successful_predictions}</b>  ({success_pct})",
            f"❌ Неудачных:            <b>{metrics.failed_predictions}</b>  ({fail_pct})",
        ]
    )

    if pending > 0:
        pending_pct = fmt_percent(pending / total, places=1)
        lines.append(f"⏳ В ожидании:          <b>{pending}</b>  ({pending_pct})")

    lines.extend(
        [
            "",
            f"📈 Среднее изменение:    <b>{change_sign}{metrics.average_price_change:.2f}%</b>",
            "",
            section_divider(),
        ]
    )

    return "\n".join(lines)
