from __future__ import annotations

from typing import TYPE_CHECKING

from moex_analyst.application.use_cases._common import tracked_tickers
from moex_analyst.presentation.bot.formatters.text import section_divider

if TYPE_CHECKING:
    from moex_analyst.core.settings import Settings

__all__ = ["format_settings"]


def format_settings(cfg: Settings) -> str:
    tickers = tracked_tickers()
    notification_status = "✅ Включены" if cfg.bot.notification_chat_id else "❌ Отключены"
    rate_limit = cfg.bot.rate_limit_per_minute

    lines: list[str] = [
        section_divider(),
        "⚙️ <b>НАСТРОЙКИ</b>",
        section_divider(),
        "",
        f"📊 Инструментов:     <b>{len(tickers)}</b>",
        "⏱ Таймфреймы:       <b>1H, 4H, 1D</b>",
        f"🔔 Оповещения:      {notification_status}",
        f"🚦 Лимит запросов:  <b>{rate_limit}/мин</b>",
        f"🌐 Окружение:       <b>{cfg.environment}</b>",
        "",
        section_divider(),
    ]

    return "\n".join(lines)
