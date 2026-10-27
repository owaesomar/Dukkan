import hashlib
import json
import secrets
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.common.exceptions import DomainError
from app.modules.auth.security import digest_secret, new_secret
from app.modules.catalog.models import Product, ProductVariant
from app.modules.customers.models import Customer
from app.modules.inventory.models import Inventory, InventoryAdjustment
from app.modules.orders.models import CheckoutIdempotency, Order, OrderItem
from app.modules.orders.schemas import (
    CheckoutRequest,
    CheckoutResponse,
    CheckoutResponseItem,
    MerchantOrderResponse,
    OrderStatus,
    PublicOrderResponse,
)
from app.modules.stores.models import Store

MAX_CHECKOUT_QUANTITY = 50


def _lines(payload: CheckoutRequest) -> dict[int, int]:
    quantities: dict[int, int] = defaultdict(int)
    for line in payload.items:
        quantities[line.variant_id] += line.quantity
    if sum(quantities.values()) > MAX_CHECKOUT_QUANTITY:
        raise DomainError(422, "Checkout quantity limit exceeded")
    return dict(quantities)


def _request_hash(payload: CheckoutRequest, quantities: dict[int, int]) -> str:
    value = {
        "email": payload.email,
        "full_name": payload.full_name,
        "phone": payload.phone,
        "shipping_address": payload.shipping_address,
        "city": payload.city,
        "postal_code": payload.postal_code,
        "country": payload.country,
        "items": sorted((variant_id, quantity) for variant_id, quantity in quantities.items()),
    }
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _checkout_items(db: Session, order_id: int, store_id: int) -> list[CheckoutResponseItem]:
    rows = db.scalars(
        select(OrderItem).where(OrderItem.store_id == store_id, OrderItem.order_id == order_id)
    ).all()
    return [
        CheckoutResponseItem(
            product_title=row.product_title,
            variant_title=row.variant_title,
            sku=row.sku,
            quantity=row.quantity,
            unit_price_minor=row.unit_price_minor,
            line_total_minor=row.line_total_minor,
        )
        for row in rows
    ]


def _checkout_response(db: Session, order: Order, tracking_token: str) -> CheckoutResponse:
    return CheckoutResponse(
        order_code=order.order_code,
        status=order.status,  # type: ignore[arg-type]
        payment_method="cash_on_delivery",
        payment_status=order.payment_status,  # type: ignore[arg-type]
        subtotal_minor=order.subtotal_minor,
        shipping_minor=order.shipping_minor,
        total_minor=order.total_minor,
        currency=order.currency,
        tracking_token=tracking_token,
        items=_checkout_items(db, order.id, order.store_id),
    )


def create_cod_order(
    db: Session, store_slug: str, idempotency_key: str, payload: CheckoutRequest
) -> CheckoutResponse:
    quantities = _lines(payload)
    request_hash = _request_hash(payload, quantities)
    with db.begin():
        store = db.scalar(select(Store).where(Store.slug == store_slug, Store.status == "active"))
        if store is None:
            raise DomainError(404, "Store not found")

        db.execute(
            pg_insert(CheckoutIdempotency)
            .values(store_id=store.id, idempotency_key=idempotency_key, request_hash=request_hash)
            .on_conflict_do_nothing(index_elements=["store_id", "idempotency_key"])
        )
        checkout_key = db.scalar(
            select(CheckoutIdempotency)
            .where(
                CheckoutIdempotency.store_id == store.id,
                CheckoutIdempotency.idempotency_key == idempotency_key,
            )
            .with_for_update()
        )
        if checkout_key is None:
            raise DomainError(409, "Could not reserve checkout request")
        if checkout_key.request_hash != request_hash:
            raise DomainError(409, "Idempotency key was already used for a different checkout")
        if checkout_key.order_id is not None:
            existing_order = db.scalar(
                select(Order).where(
                    Order.store_id == store.id,
                    Order.id == checkout_key.order_id,
                )
            )
            if existing_order is None:
                raise DomainError(409, "Prior checkout record is incomplete")
            tracking_token = new_secret()
            existing_order.tracking_token_hash = digest_secret(tracking_token)
            result = _checkout_response(db, existing_order, tracking_token)
            return result

        rows = db.execute(
            select(ProductVariant, Product, Inventory)
            .join(
                Product,
                (Product.store_id == ProductVariant.store_id)
                & (Product.id == ProductVariant.product_id),
            )
            .join(
                Inventory,
                (Inventory.store_id == ProductVariant.store_id)
                & (Inventory.variant_id == ProductVariant.id),
            )
            .where(
                ProductVariant.store_id == store.id,
                ProductVariant.id.in_(sorted(quantities)),
                ProductVariant.is_active.is_(True),
                Product.status == "published",
            )
            .order_by(ProductVariant.id)
            .with_for_update(of=Inventory)
        ).all()
        if len(rows) != len(quantities):
            raise DomainError(404, "One or more products are unavailable")
        currency = rows[0][0].currency
        if any(variant.currency != currency for variant, _, _ in rows):
            raise DomainError(422, "All checkout items must use the same currency")

        subtotal = 0
        order_items: list[OrderItem] = []
        for variant, product, inventory in rows:
            quantity = quantities[variant.id]
            available = inventory.quantity_on_hand - inventory.reserved_quantity
            if available < quantity:
                raise DomainError(409, f"Insufficient stock for {variant.sku}")
            inventory.reserved_quantity += quantity
            line_total = variant.price_minor * quantity
            subtotal += line_total
            order_items.append(
                OrderItem(
                    store_id=store.id,
                    variant_id=variant.id,
                    product_title=product.title,
                    variant_title=variant.title,
                    sku=variant.sku,
                    quantity=quantity,
                    unit_price_minor=variant.price_minor,
                    line_total_minor=line_total,
                )
            )

        customer_id = db.scalar(
            pg_insert(Customer)
            .values(
                store_id=store.id,
                email=payload.email,
                full_name=payload.full_name,
                phone=payload.phone,
            )
            .on_conflict_do_update(
                index_elements=["store_id", "email"],
                set_={"full_name": payload.full_name, "phone": payload.phone},
            )
            .returning(Customer.id)
        )
        if customer_id is None:
            raise DomainError(409, "Could not save customer details")
        tracking_token = new_secret()
        order = Order(
            store_id=store.id,
            customer_id=customer_id,
            order_code=f"DK-{secrets.token_hex(8).upper()}",
            tracking_token_hash=digest_secret(tracking_token),
            status="pending",
            payment_method="cash_on_delivery",
            payment_status="unpaid",
            subtotal_minor=subtotal,
            shipping_minor=0,
            total_minor=subtotal,
            currency=currency,
            shipping_name=payload.full_name,
            shipping_phone=payload.phone,
            shipping_address=payload.shipping_address,
            shipping_city=payload.city,
            shipping_postal_code=payload.postal_code,
            shipping_country=payload.country,
        )
        db.add(order)
        db.flush()
        for item in order_items:
            item.order_id = order.id
            db.add(item)
        checkout_key.order_id = order.id
        db.flush()
        result = _checkout_response(db, order, tracking_token)
    return result


def public_order(
    db: Session, store_slug: str, order_code: str, tracking_token: str
) -> PublicOrderResponse:
    order = db.scalar(
        select(Order)
        .join(Store, Store.id == Order.store_id)
        .where(
            Store.slug == store_slug,
            Order.order_code == order_code,
            Order.tracking_token_hash == digest_secret(tracking_token),
        )
    )
    if order is None:
        raise DomainError(404, "Order not found")
    return PublicOrderResponse(
        order_code=order.order_code,
        status=order.status,  # type: ignore[arg-type]
        payment_method="cash_on_delivery",
        payment_status=order.payment_status,  # type: ignore[arg-type]
        total_minor=order.total_minor,
        currency=order.currency,
        created_at=order.created_at,
        items=_checkout_items(db, order.id, order.store_id),
    )


def list_merchant_orders(
    db: Session, store_id: int, status_filter: OrderStatus | None, offset: int, limit: int
) -> list[MerchantOrderResponse]:
    query = (
        select(Order, Customer)
        .join(
            Customer,
            (Customer.store_id == Order.store_id) & (Customer.id == Order.customer_id),
        )
        .where(Order.store_id == store_id)
    )
    if status_filter is not None:
        query = query.where(Order.status == status_filter)
    rows = db.execute(query.order_by(Order.created_at.desc()).offset(offset).limit(limit)).all()
    return [_merchant_response(db, order, customer) for order, customer in rows]


def get_merchant_order(db: Session, store_id: int, order_id: int) -> MerchantOrderResponse:
    row = db.execute(
        select(Order, Customer)
        .join(
            Customer,
            (Customer.store_id == Order.store_id) & (Customer.id == Order.customer_id),
        )
        .where(Order.store_id == store_id, Order.id == order_id)
    ).first()
    if row is None:
        raise DomainError(404, "Order not found")
    return _merchant_response(db, row[0], row[1])


def _merchant_response(db: Session, order: Order, customer: Customer) -> MerchantOrderResponse:
    return MerchantOrderResponse(
        id=order.id,
        customer_id=customer.id,
        customer_email=customer.email,
        customer_name=customer.full_name,
        shipping_name=order.shipping_name,
        shipping_phone=order.shipping_phone,
        shipping_address=order.shipping_address,
        shipping_city=order.shipping_city,
        shipping_postal_code=order.shipping_postal_code,
        shipping_country=order.shipping_country,
        order_code=order.order_code,
        status=order.status,  # type: ignore[arg-type]
        payment_method="cash_on_delivery",
        payment_status=order.payment_status,  # type: ignore[arg-type]
        total_minor=order.total_minor,
        currency=order.currency,
        created_at=order.created_at,
        items=_checkout_items(db, order.id, order.store_id),
    )


_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending": frozenset({"confirmed", "cancelled"}),
    "confirmed": frozenset({"shipped", "cancelled"}),
    "shipped": frozenset({"delivered"}),
    "delivered": frozenset(),
    "cancelled": frozenset(),
}


def update_order_status(
    db: Session, store_id: int, order_id: int, new_status: OrderStatus, actor_user_id: int
) -> MerchantOrderResponse:
    try:
        order = db.scalar(
            select(Order).where(Order.store_id == store_id, Order.id == order_id).with_for_update()
        )
        if order is None:
            raise DomainError(404, "Order not found")
        if new_status not in _ALLOWED_TRANSITIONS[order.status]:
            raise DomainError(409, f"Cannot move order from {order.status} to {new_status}")
        if new_status in {"cancelled", "shipped"}:
            items = list(
                db.scalars(
                    select(OrderItem)
                    .where(OrderItem.store_id == store_id, OrderItem.order_id == order.id)
                    .order_by(OrderItem.variant_id)
                ).all()
            )
            inventories = list(
                db.scalars(
                    select(Inventory)
                    .where(
                        Inventory.store_id == store_id,
                        Inventory.variant_id.in_([item.variant_id for item in items]),
                    )
                    .order_by(Inventory.variant_id)
                    .with_for_update()
                ).all()
            )
            inventory_by_variant = {row.variant_id: row for row in inventories}
            for item in items:
                inventory = inventory_by_variant.get(item.variant_id)
                if inventory is None or inventory.reserved_quantity < item.quantity:
                    raise DomainError(409, "Reserved inventory no longer matches this order")
                inventory.reserved_quantity -= item.quantity
                if new_status == "shipped":
                    if inventory.quantity_on_hand < item.quantity:
                        raise DomainError(409, "Stock no longer covers this order")
                    inventory.quantity_on_hand -= item.quantity
                    db.add(
                        InventoryAdjustment(
                            store_id=store_id,
                            variant_id=item.variant_id,
                            actor_user_id=actor_user_id,
                            delta=-item.quantity,
                            reason=f"Order {order.order_code} shipped",
                        )
                    )
        order.status = new_status
        if new_status == "delivered":
            order.payment_status = "paid"
        db.flush()
        customer = db.get(Customer, order.customer_id)
        if customer is None:
            raise DomainError(404, "Customer not found")
        result = _merchant_response(db, order, customer)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return result
