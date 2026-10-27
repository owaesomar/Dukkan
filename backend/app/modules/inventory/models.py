from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (
        PrimaryKeyConstraint("store_id", "variant_id", name="pk_inventory"),
        ForeignKeyConstraint(
            ["store_id", "variant_id"],
            ["product_variants.store_id", "product_variants.id"],
            ondelete="CASCADE",
        ),
        CheckConstraint("quantity_on_hand >= 0", name="ck_inventory_on_hand_nonnegative"),
        CheckConstraint("reserved_quantity >= 0", name="ck_inventory_reserved_nonnegative"),
        CheckConstraint(
            "reserved_quantity <= quantity_on_hand", name="ck_inventory_reserved_within_stock"
        ),
    )

    store_id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[int] = mapped_column(primary_key=True)
    quantity_on_hand: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    reserved_quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class InventoryAdjustment(Base):
    __tablename__ = "inventory_adjustments"
    __table_args__ = (
        ForeignKeyConstraint(
            ["store_id", "variant_id"],
            ["product_variants.store_id", "product_variants.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT"),
        CheckConstraint("delta <> 0", name="ck_inventory_adjustments_delta_nonzero"),
        CheckConstraint(
            "length(trim(reason)) > 0", name="ck_inventory_adjustments_reason_nonblank"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    store_id: Mapped[int] = mapped_column(nullable=False, index=True)
    variant_id: Mapped[int] = mapped_column(nullable=False)
    actor_user_id: Mapped[int] = mapped_column(nullable=False)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
