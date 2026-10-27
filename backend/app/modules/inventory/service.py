from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.exceptions import DomainError
from app.modules.catalog.models import Product, ProductVariant
from app.modules.inventory.models import Inventory, InventoryAdjustment
from app.modules.inventory.schemas import InventoryAdjustmentCreate, InventoryResponse


def list_inventory(db: Session, store_id: int) -> list[InventoryResponse]:
    rows = db.execute(
        select(Inventory, ProductVariant, Product)
        .join(
            ProductVariant,
            (ProductVariant.store_id == Inventory.store_id)
            & (ProductVariant.id == Inventory.variant_id),
        )
        .join(
            Product,
            (Product.store_id == ProductVariant.store_id)
            & (Product.id == ProductVariant.product_id),
        )
        .where(Inventory.store_id == store_id)
        .order_by(Inventory.variant_id)
    ).all()
    return [
        InventoryResponse(
            store_id=inventory.store_id,
            variant_id=variant.id,
            sku=variant.sku,
            product_id=product.id,
            product_title=product.title,
            quantity_on_hand=inventory.quantity_on_hand,
            reserved_quantity=inventory.reserved_quantity,
            updated_at=inventory.updated_at,
        )
        for inventory, variant, product in rows
    ]


def adjust_inventory(
    db: Session,
    store_id: int,
    variant_id: int,
    actor_user_id: int,
    payload: InventoryAdjustmentCreate,
) -> tuple[Inventory, InventoryAdjustment]:
    inventory = db.scalar(
        select(Inventory)
        .where(Inventory.store_id == store_id, Inventory.variant_id == variant_id)
        .with_for_update()
    )
    if inventory is None:
        raise DomainError(404, "Inventory item not found")
    adjusted_quantity = inventory.quantity_on_hand + payload.delta
    if adjusted_quantity < inventory.reserved_quantity:
        raise DomainError(409, "Adjustment would reduce stock below reserved quantity")
    inventory.quantity_on_hand = adjusted_quantity
    adjustment = InventoryAdjustment(
        store_id=store_id,
        variant_id=variant_id,
        actor_user_id=actor_user_id,
        delta=payload.delta,
        reason=payload.reason,
    )
    db.add(adjustment)
    try:
        db.commit()
        db.refresh(inventory)
        db.refresh(adjustment)
    except IntegrityError as exc:
        db.rollback()
        raise DomainError(409, "Inventory adjustment conflicts with current stock") from exc
    return inventory, adjustment
