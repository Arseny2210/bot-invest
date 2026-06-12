"""Tests for the Telegram notifier (``TelegramNotifier``).

The aiogram ``Bot`` is mocked so no real Telegram API calls are made.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.enums import ParseMode

from moex_analyst.application.use_cases.dto import MarketOverview, ScoredInstrument
from moex_analyst.domain.alerts import Alert, AlertDirection, AlertSeverity, AlertType
from moex_analyst.domain.market.timeframe import Timeframe
from moex_analyst.infrastructure.notifications import (
    InMemoryDeduplicator,
    TelegramNotifier,
    format_alert,
    format_market_summary,
)
from tests.unit.alerts.conftest import make_result


@pytest.fixture
def bot() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def dedup() -> MagicMock:
    return MagicMock(spec=InMemoryDeduplicator)


@pytest.fixture
def notifier(bot: AsyncMock, dedup: MagicMock) -> TelegramNotifier:
    return TelegramNotifier(bot=bot, deduplicator=dedup)


def _alert(
    ticker: str = "SBER",
    alert_type: AlertType = AlertType.VOLUME_SPIKE,
    direction: AlertDirection = AlertDirection.BULLISH,
    severity: AlertSeverity = AlertSeverity.WARNING,
    score: float = 0.85,
    message: str = "Обнаружен всплеск объёма",
) -> Alert:
    return Alert(
        type=alert_type,
        direction=direction,
        severity=severity,
        score=score,
        message=message,
        ticker=ticker,
        timeframe=Timeframe.D1,
        as_of=datetime(2025, 6, 1, 12, tzinfo=UTC),
    )


_CHAT_ID = 12345


class TestTelegramNotifier:
    async def test_send_alert_sends_message(
        self,
        notifier: TelegramNotifier,
        bot: AsyncMock,
        dedup: MagicMock,
    ) -> None:
        dedup.check_and_mark.return_value = True
        alert = _alert()

        await notifier.send_alert(alert, chat_id=_CHAT_ID)

        expected_text = format_alert(alert)
        bot.send_message.assert_awaited_once_with(
            chat_id=_CHAT_ID,
            text=expected_text,
            parse_mode=ParseMode.HTML,
        )

    async def test_send_alert_skips_duplicate(
        self,
        notifier: TelegramNotifier,
        bot: AsyncMock,
        dedup: MagicMock,
    ) -> None:
        dedup.check_and_mark.return_value = False

        await notifier.send_alert(_alert(), chat_id=_CHAT_ID)

        bot.send_message.assert_not_awaited()

    async def test_send_alerts_sends_only_non_duplicates(
        self,
        notifier: TelegramNotifier,
        bot: AsyncMock,
        dedup: MagicMock,
    ) -> None:
        dedup.check_and_mark.side_effect = [True, False, True]
        alerts = [_alert(message="A"), _alert(message="B"), _alert(message="C")]

        await notifier.send_alerts(alerts, chat_id=_CHAT_ID)

        assert bot.send_message.await_count == 1  # only one batch after dedup

    async def test_send_alerts_empty_after_dedup_skips(
        self,
        notifier: TelegramNotifier,
        bot: AsyncMock,
        dedup: MagicMock,
    ) -> None:
        dedup.check_and_mark.return_value = False

        await notifier.send_alerts([_alert()], chat_id=_CHAT_ID)

        bot.send_message.assert_not_awaited()

    async def test_send_market_summary(
        self,
        notifier: TelegramNotifier,
        bot: AsyncMock,
    ) -> None:
        analysis = make_result()
        overview = MarketOverview(
            timeframe=Timeframe.D1,
            scored=(
                ScoredInstrument(
                    analysis=analysis,
                    alert_count=2,
                    score=0.85,
                ),
            ),
            failed=(),
        )

        await notifier.send_market_summary(overview, chat_id=_CHAT_ID)

        expected_text = format_market_summary(overview)
        bot.send_message.assert_awaited_once_with(
            chat_id=_CHAT_ID,
            text=expected_text,
            parse_mode=ParseMode.HTML,
        )
