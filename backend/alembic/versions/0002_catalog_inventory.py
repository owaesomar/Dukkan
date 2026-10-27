"""Add tenant-scoped catalog, media, and inventory tables.

Revision ID: 0002_catalog_inventory
Revises: 0001_identity_tenancy
Create Date: 2026-10-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_catalog_inventory"
down_revision: str | None = "0001_identity_tenancy"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=63), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("store_id", "id", name="uq_categories_store_id_id"),
        sa.UniqueConstraint("store_id", "slug", name="uq_categories_store_slug"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["store_id", "parent_id"],
            ["categories.store_id", "categories.id"],
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_categories_name_nonblank"),
    )
    op.create_index("ix_categories_store_id", "categories", ["store_id"])

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=5000), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("store_id", "id", name="uq_products_store_id_id"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["store_id", "category_id"],
            ["categories.store_id", "categories.id"],
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("length(trim(title)) > 0", name="ck_products_title_nonblank"),
        sa.CheckConstraint(
            "status IN ('draft', 'published', 'archived')", name="ck_products_status"
        ),
    )
    op.create_index("ix_products_store_status", "products", ["store_id", "status"])
    op.create_index("ix_products_store_category", "products", ["store_id", "category_id"])

    op.create_table(
        "product_variants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False, server_default="Default"),
        sa.Column("price_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="BDT"),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("store_id", "id", name="uq_product_variants_store_id_id"),
        sa.UniqueConstraint("store_id", "sku", name="uq_product_variants_store_sku"),
        sa.ForeignKeyConstraint(
            ["store_id", "product_id"],
            ["products.store_id", "products.id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("length(trim(sku)) > 0", name="ck_product_variants_sku_nonblank"),
        sa.CheckConstraint("price_minor >= 0", name="ck_product_variants_price_nonnegative"),
        sa.CheckConstraint(
            "length(currency) = 3 AND currency = upper(currency)",
            name="ck_product_variants_currency",
        ),
    )
    op.create_index(
        "ix_product_variants_store_product", "product_variants", ["store_id", "product_id"]
    )

    op.create_table(
        "inventory",
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("variant_id", sa.Integer(), nullable=False),
        sa.Column("quantity_on_hand", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reserved_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("store_id", "variant_id", name="pk_inventory"),
        sa.ForeignKeyConstraint(
            ["store_id", "variant_id"],
            ["product_variants.store_id", "product_variants.id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("quantity_on_hand >= 0", name="ck_inventory_on_hand_nonnegative"),
        sa.CheckConstraint("reserved_quantity >= 0", name="ck_inventory_reserved_nonnegative"),
        sa.CheckConstraint(
            "reserved_quantity <= quantity_on_hand", name="ck_inventory_reserved_within_stock"
        ),
    )

    op.create_table(
        "inventory_adjustments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("variant_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["store_id", "variant_id"],
            ["product_variants.store_id", "product_variants.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("delta <> 0", name="ck_inventory_adjustments_delta_nonzero"),
        sa.CheckConstraint(
            "length(trim(reason)) > 0", name="ck_inventory_adjustments_reason_nonblank"
        ),
    )
    op.create_index("ix_inventory_adjustments_store_id", "inventory_adjustments", ["store_id"])

    op.create_table(
        "product_media",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Integer(), nullable=False),
        sa.Column("object_key", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=40), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("alt_text", sa.String(length=250), nullable=False, server_default=""),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("store_id", "id", name="uq_product_media_store_id_id"),
        sa.UniqueConstraint("object_key", name="uq_product_media_object_key"),
        sa.ForeignKeyConstraint(
            ["store_id", "product_id"],
            ["products.store_id", "products.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("byte_size > 0 AND byte_size <= 8388608", name="ck_product_media_size"),
        sa.CheckConstraint(
            "content_type IN ('image/jpeg', 'image/png', 'image/webp')",
            name="ck_product_media_content_type",
        ),
    )
    op.create_index("ix_product_media_store_product", "product_media", ["store_id", "product_id"])


def downgrade() -> None:
    op.drop_index("ix_product_media_store_product", table_name="product_media")
    op.drop_table("product_media")
    op.drop_index("ix_inventory_adjustments_store_id", table_name="inventory_adjustments")
    op.drop_table("inventory_adjustments")
    op.drop_table("inventory")
    op.drop_index("ix_product_variants_store_product", table_name="product_variants")
    op.drop_table("product_variants")
    op.drop_index("ix_products_store_category", table_name="products")
    op.drop_index("ix_products_store_status", table_name="products")
    op.drop_table("products")
    op.drop_index("ix_categories_store_id", table_name="categories")
    op.drop_table("categories")
