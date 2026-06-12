from __future__ import annotations

from moex_analyst.presentation.bot.formatters.text import escape

__all__ = ["format_error", "format_help", "format_start"]


def format_start(first_name: str | None = None) -> str:
    greeting = f", {escape(first_name)}" if first_name else ""
    return (
        f"👋 <b>Привет{greeting}!</b>\n\n"
        "🤖 <b>MOEX Analyst</b>\n\n"
        "Технический анализ инструментов Московской Биржи:\n"
        "• 📊 Тренды и рыночная структура\n"
        "• 📉 Уровни поддержки и сопротивления\n"
        "• 📐 Индикаторы (RSI, EMA, ATR)\n"
        "• 🎯 Вероятностный прогноз\n"
        "• 🚨 Сигналы и оповещения\n\n"
        "Выберите действие через меню ниже ⬇️"
    )


def format_help() -> str:
    return (
        "🛟 <b>ПОМОЩЬ</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Разделы</b>\n\n"
        "📈 <b>Анализ акции</b>\n"
        "   Выберите инструмент из списка\n\n"
        "📊 <b>Состояние рынка</b>\n"
        "   Обзор всех инструментов\n\n"
        "⭐ <b>Избранное</b>\n"
        "   Быстрый доступ к инструментам\n\n"
        "🎯 <b>Сигналы</b>\n"
        "   Активные оповещения\n\n"
        "📋 <b>Статистика</b>\n"
        "   Точность прогнозов\n\n"
        "⚙️ <b>Настройки</b>\n"
        "   Параметры бота\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Таймфреймы</b>\n"
        "1H — 1 час  |  4H — 4 часа  |  1D — 1 день\n\n"
        "<i>Выберите нужный раздел через меню ниже.</i>"
    )


def format_error(message: str) -> str:
    return f"⚠️ <b>Ошибка</b>\n\n{escape(message)}"
