"""SQLAlchemy implementation of the Unit of Work port.

Owns the lifecycle of a single :class:`AsyncSession`: opens it on enter, rolls
back on error or on exit-without-commit, and always closes it. Commit is
explicit — callers commit deliberately, never implicitly on context exit, to
avoid persisting partially-applied work.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from moex_analyst.application.ports.unit_of_work import UnitOfWork

if TYPE_CHECKING:
    from types import TracebackType

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

__all__ = ["SqlAlchemyUnitOfWork"]


class SqlAlchemyUnitOfWork(UnitOfWork):
    """Unit of Work backed by a SQLAlchemy async session."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self._committed = False

    @property
    def session(self) -> AsyncSession:
        """The active session. Valid only inside the ``async with`` block."""
        if self._session is None:
            raise RuntimeError("UnitOfWork is not active; use 'async with uow:'")
        return self._session

    async def __aenter__(self) -> Self:
        if self._session is not None:
            raise RuntimeError("UnitOfWork is not re-entrant")
        self._session = self._session_factory()
        self._committed = False
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        session = self._session
        if session is None:
            return
        try:
            if exc_type is not None or not self._committed:
                await session.rollback()
        finally:
            await session.close()
            self._session = None
            self._committed = False

    async def commit(self) -> None:
        await self.session.commit()
        self._committed = True

    async def rollback(self) -> None:
        await self.session.rollback()
        self._committed = False
