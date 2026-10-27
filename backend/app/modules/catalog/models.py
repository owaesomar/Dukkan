from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("store_id", "id", name="uq_categories_store_id_id"),
        UniqueConstraint("store_id", "slug", name="uq_categories_store_slug"),
        ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        ForeignKeyConstraint(
            ["store_id", "parent_id"],
            ["categories.store_id", "categories.id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint("length(trim(name)) > 0", name="ck_categories_name_nonblank"),
        Index("ix_categories_store_id", "store_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(nullable=False)
    parent_id: Mapped[int | None] = mapped_column(nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(63), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("store_id", "id", name="uq_products_store_id_id"),
        ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        ForeignKeyConstraint(
            ["store_id", "category_id"],
            ["categories.store_id", "categories.id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint("length(trim(title)) > 0", name="ck_products_title_nonblank"),
        CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_products_status"),
        Index("ix_products_store_status", "store_id", "status"),
        Index("ix_products_store_category", "store_id", "category_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(nullable=False)
    category_id: Mapped[int | None] = mapped_column(nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(5000))
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", server_default=text("'draft'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class ProductVariant(Base):
    __tablename__ = "product_variants"
    __table_args__ = (
        UniqueConstraint("store_id", "id", name="uq_product_variants_store_id_id"),
        UniqueConstraint("store_id", "sku", name="uq_product_variants_store_sku"),
        ForeignKeyConstraint(
            ["store_id", "product_id"],
            ["products.store_id", "products.id"],
            ondelete="CASCADE",
        ),
        CheckConstraint("length(trim(sku)) > 0", name="ck_product_variants_sku_nonblank"),
        CheckConstraint("price_minor >= 0", name="ck_product_variants_price_nonnegative"),
        CheckConstraint(
            "length(currency) = 3 AND currency = upper(currency)",
            name="ck_product_variants_currency",
        ),
        Index("ix_product_variants_store_product", "store_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(nullable=False)
    product_id: Mapped[int] = mapped_column(nullable=False)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(
        String(100), nullable=False, default="Default", server_default=text("'Default'")
    )
    price_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="BDT", server_default=text("'BDT'")
    )
    options: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ProductMedia(Base):
    __tablename__ = "product_media"
    __table_args__ = (
        UniqueConstraint("store_id", "id", name="uq_product_media_store_id_id"),
        UniqueConstraint("object_key", name="uq_product_media_object_key"),
        ForeignKeyConstraint(
            ["store_id", "product_id"],
            ["products.store_id", "products.id"],
            ondelete="CASCADE",
        ),
        CheckConstraint("byte_size > 0 AND byte_size <= 8388608", name="ck_product_media_size"),
        CheckConstraint(
            "content_type IN ('image/jpeg', 'image/png', 'image/webp')",
            name="ck_product_media_content_type",
        ),
        Index("ix_product_media_store_product", "store_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(nullable=False)
    product_id: Mapped[int] = mapped_column(nullable=False)
    uploaded_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(40), nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    alt_text: Mapped[str] = mapped_column(
        String(250), nullable=False, default="", server_default=text("''")
    )
    position: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
