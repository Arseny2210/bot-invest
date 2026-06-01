"""Generic async repository base for SQLAlchemy ORM models.

Concrete per-aggregate repositories (added once domain models exist) subclass
this, set the ``model`` class attribute, and add query methods specific to
their aggregate. The base provides the common, model-agnostic operations.

The repository never opens transactions or commits — that is the Unit of
Work's responsibility. It operates on the session it is given.
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any

from sqlalchemy import func, select

from moex_analyst.infrastructure.db.base import Base

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ["BaseRepository"]


class BaseRepository[ModelT: Base](ABC):
    """Common CRUD operations shared by all SQLAlchemy repositories.

    Subclasses must set ``model`` to their ORM class::

        class CandleRepository(BaseRepository[Candle]):
            model = Candle
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: ModelT) -> ModelT:
        """Stage ``entity`` for insert and flush to assign generated keys."""
        self._session.add(entity)
        await self._session.flush((entity,))
        return entity

    async def add_all(self, entities: Sequence[ModelT]) -> Sequence[ModelT]:
        """Stage many entities and flush once."""
        self._session.add_all(entities)
        await self._session.flush(entities)
        return entities

    async def get(self, pk: Any) -> ModelT | None:
        """Fetch by primary key, or ``None`` if absent."""
        return await self._session.get(self.model, pk)

    async def delete(self, entity: ModelT) -> None:
        """Mark ``entity`` for deletion."""
        await self._session.delete(entity)

    async def exists(self, pk: Any) -> bool:
        """Return whether a row with primary key ``pk`` exists."""
        return await self.get(pk) is not None

    async def list(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Sequence[ModelT]:
        """Return rows, optionally paginated. No implicit ordering."""
        stmt = select(self.model)
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        """Return the total number of rows for this model."""
        stmt = select(func.count()).select_from(self.model)
        result = await self._session.execute(stmt)
        return result.scalar_one()
