"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-08-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "instruments",
        sa.Column("canonical_id", sa.String(32), primary_key=True),
        sa.Column("display_symbol", sa.String(32), index=True),
        sa.Column("asset_class", sa.String(64)),
        sa.Column("tradable", sa.Boolean(), default=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "broker_accounts",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(128)),
        sa.Column("account_type", sa.String(16)),
        sa.Column("metaapi_account_id", sa.String(128)),
        sa.Column("broker_server", sa.String(256)),
        sa.Column("encrypted_token", sa.Text()),
        sa.Column("is_connected", sa.Boolean(), default=False),
        sa.Column("last_health_check", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "operator_settings",
        sa.Column("id", sa.Integer(), primary_key=True, default=1),
        sa.Column("language", sa.String(8), server_default="en"),
        sa.Column("theme", sa.String(16), server_default="dark"),
        sa.Column("risk_per_trade_r", sa.Float(), server_default="1.0"),
        sa.Column("spread_limit_pips", sa.Float(), server_default="3.0"),
        sa.Column("daily_loss_limit_r", sa.Float(), server_default="5.0"),
        sa.Column("consecutive_loss_limit", sa.Integer(), server_default="3"),
        sa.Column("price_divergence_threshold_pct", sa.Float(), server_default="0.15"),
        sa.Column("exposure_cap_r", sa.Float(), nullable=True),
        sa.Column("live_promotion_confirmation_method", sa.String(16), server_default="pin"),
        sa.Column("live_promotion_pin_hash", sa.String(256), nullable=True),
        sa.Column("notification_prefs", sa.JSON(), server_default="{}"),
        sa.Column("telegram_chat_id", sa.String(64), nullable=True),
        sa.Column("telegram_link_code", sa.String(16), nullable=True),
        sa.Column("emergency_halt", sa.Boolean(), server_default="false"),
        sa.Column("feed_health", sa.JSON(), server_default="{}"),
    )

    op.create_table(
        "recommendations",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column("canonical_id", sa.String(32), index=True),
        sa.Column("timeframe", sa.String(8)),
        sa.Column("direction", sa.String(8)),
        sa.Column("analytical_bias", sa.String(8)),
        sa.Column("plan_type", sa.String(32)),
        sa.Column("execution_status", sa.String(32)),
        sa.Column("fill_rule", sa.String(32)),
        sa.Column("entry_zone_low", sa.Float()),
        sa.Column("entry_zone_high", sa.Float()),
        sa.Column("preferred_entry", sa.Float()),
        sa.Column("stop_loss", sa.Float()),
        sa.Column("take_profits", sa.JSON()),
        sa.Column("invalidation_rule", sa.Text()),
        sa.Column("activation_rule", sa.Text(), nullable=True),
        sa.Column("activation_condition", sa.Text(), nullable=True),
        sa.Column("validity_candles", sa.Integer()),
        sa.Column("analysis_mode", sa.String(32)),
        sa.Column("confidence_label", sa.String(64)),
        sa.Column("similar_past_cases", sa.JSON()),
        sa.Column("gate_results", sa.JSON()),
        sa.Column("chart_snapshots", sa.JSON()),
        sa.Column("strategy_id", sa.String(64), nullable=True),
        sa.Column("backtest_stats", sa.JSON(), nullable=True),
        sa.Column("outcome", sa.String(32), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "agent_memory",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column("recommendation_id", sa.UUID(as_uuid=False), nullable=True),
        sa.Column("canonical_id", sa.String(32), index=True),
        sa.Column("context_text", sa.Text()),
        sa.Column("outcome", sa.String(32)),
        sa.Column("embedding", Vector(1536)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("agent_memory")
    op.drop_table("recommendations")
    op.drop_table("operator_settings")
    op.drop_table("broker_accounts")
    op.drop_table("instruments")
