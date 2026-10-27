"""Add platform admin, subscriptions, and audit events.

Revision ID: 0004_saas_management
Revises: 0003_orders_checkout
Create Date: 2026-10-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_saas_management"
down_revision: str | None = "0003_orders_checkout"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_store_memberships_role", "store_memberships", type_="check")
    op.create_check_constraint(
        "ck_store_memberships_role",
        "store_memberships",
        "role IN ('owner', 'admin', 'manager', 'catalog', 'fulfillment', 'staff', 'viewer')",
    )

    op.create_table(
        "platform_admin_roles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("granted_by_user_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("user_id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["granted_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_platform_admin_roles_is_active", "platform_admin_roles", ["is_active"])

    op.create_table(
        "subscription_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("price_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="BDT", nullable=False),
        sa.Column(
            "billing_interval", sa.String(length=16), server_default="monthly", nullable=False
        ),
        sa.Column("limits", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("code", name="uq_subscription_plans_code"),
        sa.CheckConstraint("price_minor >= 0", name="ck_subscription_plans_price_nonnegative"),
        sa.CheckConstraint(
            "currency = upper(currency) AND length(currency) = 3",
            name="ck_subscription_plans_currency",
        ),
        sa.CheckConstraint(
            "billing_interval IN ('monthly', 'yearly')",
            name="ck_subscription_plans_interval",
        ),
    )

    op.create_table(
        "store_subscriptions",
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), server_default="active", nullable=False),
        sa.Column("cancellation_reason", sa.String(length=500), nullable=True),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("store_id"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["subscription_plans.id"], ondelete="RESTRICT"),
        sa.CheckConstraint(
            "status IN ('active', 'past_due', 'canceled')",
            name="ck_store_subscriptions_status",
        ),
    )

    op.create_table(
        "platform_audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("resource_type", sa.String(length=40), nullable=False),
        sa.Column("resource_id", sa.String(length=80), nullable=False),
        sa.Column("details", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_platform_audit_events_created_at", "platform_audit_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_platform_audit_events_created_at", table_name="platform_audit_events")
    op.drop_table("platform_audit_events")
    op.drop_table("store_subscriptions")
    op.drop_table("subscription_plans")
    op.drop_index("ix_platform_admin_roles_is_active", table_name="platform_admin_roles")
    op.drop_table("platform_admin_roles")
    op.drop_constraint("ck_store_memberships_role", "store_memberships", type_="check")
    op.create_check_constraint(
        "ck_store_memberships_role",
        "store_memberships",
        "role IN ('owner', 'admin', 'catalog', 'fulfillment', 'viewer')",
    )
