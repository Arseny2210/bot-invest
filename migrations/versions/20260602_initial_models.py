"""Create analysis_records, alert_records, forecast_records, forecast_outcomes

Revision ID: 001_create_tables
Revises:
Create Date: 2026-06-02 10:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "001_create_tables"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "analysis_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(32), nullable=False, index=True),
        sa.Column("timeframe", sa.String(4), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trend_direction", sa.String(16), nullable=False),
        sa.Column("trend_strength", sa.String(16), nullable=False),
        sa.Column("trend_score", sa.Float(), nullable=False),
        sa.Column("bullish_probability", sa.Float(), nullable=False),
        sa.Column("bearish_probability", sa.Float(), nullable=False),
        sa.Column("sideways_probability", sa.Float(), nullable=False),
        sa.Column("rsi", sa.Numeric(8, 4), nullable=True),
        sa.Column("atr", sa.Numeric(16, 6), nullable=True),
        sa.Column("ema20", sa.Numeric(16, 6), nullable=True),
        sa.Column("ema50", sa.Numeric(16, 6), nullable=True),
        sa.Column("support_levels", JSONB(), nullable=False, server_default="[]"),
        sa.Column("resistance_levels", JSONB(), nullable=False, server_default="[]"),
        sa.Column("volume_state", sa.String(16), nullable=False),
        sa.Column("market_structure", sa.Text(), nullable=False, server_default=""),
        sa.Column("candles_analysed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_analysis_records")),
    )

    op.create_table(
        "alert_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(32), nullable=False, index=True),
        sa.Column("timeframe", sa.String(4), nullable=False),
        sa.Column("alert_type", sa.String(32), nullable=False),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("message_hash", sa.String(64), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alert_records")),
    )

    op.create_table(
        "forecast_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(32), nullable=False, index=True),
        sa.Column("timeframe", sa.String(4), nullable=False),
        sa.Column("prediction_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("price_at_prediction", sa.Numeric(16, 6), nullable=False),
        sa.Column("bullish_probability", sa.Float(), nullable=False),
        sa.Column("bearish_probability", sa.Float(), nullable=False),
        sa.Column("sideways_probability", sa.Float(), nullable=False),
        sa.Column("forecast_horizon_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column(
            "status",
            sa.String(16),
            nullable=False,
            server_default="PENDING",
            index=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_forecast_records")),
    )

    op.create_table(
        "forecast_outcomes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "forecast_id",
            sa.Integer(),
            sa.ForeignKey("forecast_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("evaluation_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_price", sa.Numeric(16, 6), nullable=False),
        sa.Column("price_change_percent", sa.Float(), nullable=False),
        sa.Column("result", sa.String(16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_forecast_outcomes")),
    )


def downgrade() -> None:
    op.drop_table("forecast_outcomes")
    op.drop_table("forecast_records")
    op.drop_table("alert_records")
    op.drop_table("analysis_records")
