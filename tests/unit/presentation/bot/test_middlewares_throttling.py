from unittest.mock import AsyncMock, MagicMock

from aiogram.types import CallbackQuery, Message

from moex_analyst.presentation.bot.middlewares.throttling import ThrottlingMiddleware


class TestThrottlingMiddleware:
    async def _make_event(self, spec: type, user_id: int = 1) -> MagicMock:
        ev = MagicMock(spec=spec)
        ev.from_user = MagicMock()
        ev.from_user.id = user_id
        ev.answer = AsyncMock()
        ev.text = "test"
        ev.data = None
        return ev

    async def test_allows_within_limit(self) -> None:
        mw = ThrottlingMiddleware(limit_per_minute=3)
        handler = AsyncMock(return_value="ok")

        for _ in range(3):
            event = await self._make_event(Message, user_id=10)
            result = await mw(handler, event, {})
            assert result == "ok"

        assert handler.await_count == 3

    async def test_blocks_over_limit(self) -> None:
        mw = ThrottlingMiddleware(limit_per_minute=2)
        handler = AsyncMock(return_value="ok")

        for _ in range(2):
            event = await self._make_event(Message, user_id=20)
            await mw(handler, event, {})

        block_event = await self._make_event(Message, user_id=20)
        result = await mw(handler, block_event, {})

        assert result is None
        assert handler.await_count == 2

    async def test_blocks_and_notifies_callback(self) -> None:
        mw = ThrottlingMiddleware(limit_per_minute=0)
        handler = AsyncMock()
        event = await self._make_event(CallbackQuery, user_id=30)

        await mw(handler, event, {})

        handler.assert_not_awaited()
        event.answer.assert_awaited_once()

    async def test_blocks_and_notifies_message(self) -> None:
        mw = ThrottlingMiddleware(limit_per_minute=0)
        handler = AsyncMock()
        event = await self._make_event(Message, user_id=40)

        await mw(handler, event, {})

        handler.assert_not_awaited()
        event.answer.assert_awaited_once()

    async def test_different_users_independent_limits(self) -> None:
        mw = ThrottlingMiddleware(limit_per_minute=1)
        handler = AsyncMock(return_value="ok")

        for uid in (50, 60, 70):
            event = await self._make_event(Message, user_id=uid)
            result = await mw(handler, event, {})
            assert result == "ok"

        assert handler.await_count == 3

    async def test_allows_after_window_expires(self) -> None:
        mw = ThrottlingMiddleware(limit_per_minute=1)
        handler = AsyncMock(return_value="ok")

        event1 = await self._make_event(Message, user_id=80)
        await mw(handler, event1, {})
        assert handler.await_count == 1

        event2 = await self._make_event(Message, user_id=80)
        result = await mw(handler, event2, {})
        assert result is None
        assert handler.await_count == 1

        mw._hits[80].clear()

        event3 = await self._make_event(Message, user_id=80)
        result = await mw(handler, event3, {})
        assert result == "ok"
        assert handler.await_count == 2

    async def test_no_user_id_always_passes(self) -> None:
        mw = ThrottlingMiddleware(limit_per_minute=0)
        handler = AsyncMock(return_value="ok")
        event = MagicMock(spec=Message)
        event.from_user = None

        result = await mw(handler, event, {})

        assert result == "ok"
        handler.assert_awaited_once()
