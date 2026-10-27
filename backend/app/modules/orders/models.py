from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("store_id", "id", name="uq_orders_store_id_id"),
        UniqueConstraint("store_id", "order_code", name="uq_orders_store_code"),
        UniqueConstraint("tracking_token_hash", name="uq_orders_tracking_token_hash"),
        ForeignKeyConstraint(
            ["store_id", "customer_id"],
            ["customers.store_id", "customers.id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled')",
            name="ck_orders_status",
        ),
        CheckConstraint("payment_method = 'cash_on_delivery'", name="ck_orders_payment_method"),
        CheckConstraint("payment_status IN ('unpaid', 'paid')", name="ck_orders_payment_status"),
        CheckConstraint("subtotal_minor >= 0", name="ck_orders_subtotal_nonnegative"),
        CheckConstraint("shipping_minor >= 0", name="ck_orders_shipping_nonnegative"),
        CheckConstraint("total_minor >= 0", name="ck_orders_total_nonnegative"),
        CheckConstraint(
            "length(currency) = 3 AND currency = upper(currency)", name="ck_orders_currency"
        ),
        Index("ix_orders_store_status_created", "store_id", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(nullable=False)
    customer_id: Mapped[int] = mapped_column(nullable=False)
    order_code: Mapped[str] = mapped_column(String(32), nullable=False)
    tracking_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default=text("'pending'")
    )
    payment_method: Mapped[str] = mapped_column(
        String(32), nullable=False, default="cash_on_delivery"
    )
    payment_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="unpaid", server_default=text("'unpaid'")
    )
    subtotal_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    shipping_minor: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default=text("0")
    )
    total_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    shipping_name: Mapped[str] = mapped_column(String(160), nullable=False)
    shipping_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    shipping_address: Mapped[str] = mapped_column(Text, nullable=False)
    shipping_city: Mapped[str] = mapped_column(String(100), nullable=False)
    shipping_postal_code: Mapped[str | None] = mapped_column(String(24))
    shipping_country: Mapped[str] = mapped_column(String(2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        ForeignKeyConstraint(
            ["store_id", "order_id"], ["orders.store_id", "orders.id"], ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["store_id", "variant_id"],
            ["product_variants.store_id", "product_variants.id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        CheckConstraint("unit_price_minor >= 0", name="ck_order_items_price_nonnegative"),
        CheckConstraint("line_total_minor >= 0", name="ck_order_items_total_nonnegative"),
        Index("ix_order_items_store_order", "store_id", "order_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(nullable=False)
    order_id: Mapped[int] = mapped_column(nullable=False)
    variant_id: Mapped[int] = mapped_column(nullable=False)
    product_title: Mapped[str] = mapped_column(String(200), nullable=False)
    variant_title: Mapped[str] = mapped_column(String(100), nullable=False)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    line_total_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)


class CheckoutIdempotency(Base):
    __tablename__ = "checkout_idempotency"
    __table_args__ = (
        PrimaryKeyConstraint("store_id", "idempotency_key", name="pk_checkout_idempotency"),
        ForeignKeyConstraint(
            ["store_id", "order_id"], ["orders.store_id", "orders.id"], ondelete="CASCADE"
        ),
        UniqueConstraint("store_id", "order_id", name="uq_checkout_idempotency_store_order"),
    )

    store_id: Mapped[int] = mapped_column(primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    order_id: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
