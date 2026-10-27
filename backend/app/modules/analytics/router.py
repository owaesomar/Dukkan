from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.db.dependencies import SessionDep
from app.modules.analytics.schemas import StoreAnalyticsResponse
from app.modules.catalog.models import Product, ProductVariant
from app.modules.customers.models import Customer
from app.modules.inventory.models import Inventory
from app.modules.memberships.authorization import OrdersReadDep
from app.modules.orders.models import Order, OrderItem

router = APIRouter(prefix="/stores/{store_id}/analytics", tags=["analytics"])


@router.get("/overview", response_model=StoreAnalyticsResponse)
def get_store_analytics(
    db: SessionDep,
    access: OrdersReadDep,
    start: Annotated[datetime | None, Query()] = None,
    end: Annotated[datetime | None, Query()] = None,
) -> StoreAnalyticsResponse:
    now = datetime.now(UTC)
    start = start or now - timedelta(days=30)
    end = end or now + timedelta(seconds=1)
    if start.tzinfo is None or end.tzinfo is None or start >= end:
        raise HTTPException(status_code=422, detail="Use a valid timezone-aware date range")

    store_id = access.store.id
    period = (Order.store_id == store_id, Order.created_at >= start, Order.created_at < end)
    orders_count = db.scalar(select(func.count(Order.id)).where(*period)) or 0
    open_count = (
        db.scalar(
            select(func.count(Order.id)).where(
                *period, Order.status.in_(["pending", "confirmed", "shipped"])
            )
        )
        or 0
    )
    delivered_count = (
        db.scalar(select(func.count(Order.id)).where(*period, Order.status == "delivered")) or 0
    )
    revenue_rows = db.execute(
        select(Order.currency, func.sum(Order.total_minor))
        .where(*period, Order.payment_status == "paid")
        .group_by(Order.currency)
    ).all()
    units_sold = (
        db.scalar(
            select(func.coalesce(func.sum(OrderItem.quantity), 0))
            .join(Order, (Order.store_id == OrderItem.store_id) & (Order.id == OrderItem.order_id))
            .where(*period, Order.payment_status == "paid")
        )
        or 0
    )
    new_customers = (
        db.scalar(
            select(func.count(Customer.id)).where(
                Customer.store_id == store_id,
                Customer.created_at >= start,
                Customer.created_at < end,
            )
        )
        or 0
    )
    products_count = (
        db.scalar(
            select(func.count(Product.id)).where(
                Product.store_id == store_id, Product.status == "published"
            )
        )
        or 0
    )
    low_stock_count = (
        db.scalar(
            select(func.count())
            .select_from(Inventory)
            .join(
                ProductVariant,
                (ProductVariant.store_id == Inventory.store_id)
                & (ProductVariant.id == Inventory.variant_id),
            )
            .where(
                Inventory.store_id == store_id,
                ProductVariant.is_active.is_(True),
                Inventory.quantity_on_hand - Inventory.reserved_quantity <= 5,
            )
        )
        or 0
    )
    return StoreAnalyticsResponse(
        period_start=start,
        period_end=end,
        orders_count=orders_count,
        open_orders_count=open_count,
        delivered_orders_count=delivered_count,
        units_sold=units_sold,
        paid_revenue_by_currency={currency: int(amount or 0) for currency, amount in revenue_rows},
        new_customers_count=new_customers,
        published_products_count=products_count,
        low_stock_variants_count=low_stock_count,
    )
