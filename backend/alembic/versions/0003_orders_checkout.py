"""Add customers, COD orders, and checkout idempotency.

Revision ID: 0003_orders_checkout
Revises: 0002_catalog_inventory
Create Date: 2026-10-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_orders_checkout"
down_revision: str | None = "0002_catalog_inventory"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("store_id", "id", name="uq_customers_store_id_id"),
        sa.UniqueConstraint("store_id", "email", name="uq_customers_store_email"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("order_code", sa.String(length=32), nullable=False),
        sa.Column("tracking_token_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column(
            "payment_method",
            sa.String(length=32),
            nullable=False,
            server_default="cash_on_delivery",
        ),
        sa.Column("payment_status", sa.String(length=16), nullable=False, server_default="unpaid"),
        sa.Column("subtotal_minor", sa.BigInteger(), nullable=False),
        sa.Column("shipping_minor", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("total_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("shipping_name", sa.String(length=160), nullable=False),
        sa.Column("shipping_phone", sa.String(length=32), nullable=False),
        sa.Column("shipping_address", sa.Text(), nullable=False),
        sa.Column("shipping_city", sa.String(length=100), nullable=False),
        sa.Column("shipping_postal_code", sa.String(length=24), nullable=True),
        sa.Column("shipping_country", sa.String(length=2), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("store_id", "id", name="uq_orders_store_id_id"),
        sa.UniqueConstraint("store_id", "order_code", name="uq_orders_store_code"),
        sa.UniqueConstraint("tracking_token_hash", name="uq_orders_tracking_token_hash"),
        sa.ForeignKeyConstraint(
            ["store_id", "customer_id"],
            ["customers.store_id", "customers.id"],
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled')",
            name="ck_orders_status",
        ),
        sa.CheckConstraint("payment_method = 'cash_on_delivery'", name="ck_orders_payment_method"),
        sa.CheckConstraint("payment_status IN ('unpaid', 'paid')", name="ck_orders_payment_status"),
        sa.CheckConstraint("subtotal_minor >= 0", name="ck_orders_subtotal_nonnegative"),
        sa.CheckConstraint("shipping_minor >= 0", name="ck_orders_shipping_nonnegative"),
        sa.CheckConstraint("total_minor >= 0", name="ck_orders_total_nonnegative"),
        sa.CheckConstraint(
            "length(currency) = 3 AND currency = upper(currency)", name="ck_orders_currency"
        ),
    )
    op.create_index(
        "ix_orders_store_status_created", "orders", ["store_id", "status", "created_at"]
    )

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("variant_id", sa.Integer(), nullable=False),
        sa.Column("product_title", sa.String(length=200), nullable=False),
        sa.Column("variant_title", sa.String(length=100), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_minor", sa.BigInteger(), nullable=False),
        sa.Column("line_total_minor", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["store_id", "order_id"], ["orders.store_id", "orders.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["store_id", "variant_id"],
            ["product_variants.store_id", "product_variants.id"],
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        sa.CheckConstraint("unit_price_minor >= 0", name="ck_order_items_price_nonnegative"),
        sa.CheckConstraint("line_total_minor >= 0", name="ck_order_items_total_nonnegative"),
    )
    op.create_index("ix_order_items_store_order", "order_items", ["store_id", "order_id"])

    op.create_table(
        "checkout_idempotency",
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("store_id", "idempotency_key", name="pk_checkout_idempotency"),
        sa.ForeignKeyConstraint(
            ["store_id", "order_id"], ["orders.store_id", "orders.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("store_id", "order_id", name="uq_checkout_idempotency_store_order"),
    )


def downgrade() -> None:
    op.drop_table("checkout_idempotency")
    op.drop_index("ix_order_items_store_order", table_name="order_items")
    op.drop_table("order_items")
    op.drop_index("ix_orders_store_status_created", table_name="orders")
    op.drop_table("orders")
    op.drop_table("customers")
