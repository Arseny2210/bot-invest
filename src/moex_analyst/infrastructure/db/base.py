"""SQLAlchemy declarative base and shared mapping building blocks.

The declarative ``Base`` carries an explicit constraint/index naming
convention so that Alembic autogenerate emits deterministic, downgrade-safe
names across machines. ``datetime`` is mapped to a timezone-aware column type
to enforce the project-wide "UTC everywhere" rule.

No business entities are defined here — only reusable infrastructure.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

__all__ = ["Base", "TimestampMixin", "metadata"]

# Deterministic names for indexes, unique/check/foreign keys and primary keys.
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    """Declarative base for all ORM models.

    Subclasses are defined in later stages under ``db/models``. Mapping all
    ``datetime`` columns to ``TIMESTAMP WITH TIME ZONE`` keeps persisted
    instants unambiguous.
    """

    metadata = metadata
    type_annotation_map: ClassVar[dict[type, Any]] = {
        datetime: DateTime(timezone=True),
    }


class TimestampMixin:
    """Adds DB-managed ``created_at`` / ``updated_at`` timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
