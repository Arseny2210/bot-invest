"""Unit of Work port — the transactional boundary abstraction.

This interface lives in the application layer and is intentionally free of any
SQLAlchemy / persistence detail. Use cases depend on this abstraction; the
concrete implementation lives in
:mod:`moex_analyst.infrastructure.db.unit_of_work`.

Concrete aggregate repositories will be exposed on this port in a later stage,
once domain entities exist.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from types import TracebackType

__all__ = ["UnitOfWork"]


class UnitOfWork(ABC):
    """Manages a single atomic transaction as an async context manager.

    Usage::

        async with uow:
            ...                 # do work via repositories
            await uow.commit()

    Leaving the context without committing rolls back; any exception inside the
    block triggers a rollback as well.
    """

    @abstractmethod
    async def __aenter__(self) -> Self:
        """Begin the unit of work and return it."""

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Finalize the unit of work (rollback on error; always release)."""

    @abstractmethod
    async def commit(self) -> None:
        """Persist all changes made within this unit of work."""

    @abstractmethod
    async def rollback(self) -> None:
        """Discard all changes made within this unit of work."""
