from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from app.db.dependencies import SessionDep
from app.modules.auth.dependencies import require_csrf
from app.modules.customers.models import Customer
from app.modules.customers.schemas import CustomerResponse
from app.modules.memberships.authorization import OrdersFulfillDep, OrdersReadDep
from app.modules.orders import service
from app.modules.orders.schemas import (
    MerchantOrderResponse,
    OrderStatus,
    OrderStatusUpdate,
)

router = APIRouter(tags=["orders"])


@router.get("/stores/{store_id}/orders", response_model=list[MerchantOrderResponse])
def list_orders(
    store_id: int,
    db: SessionDep,
    access: OrdersReadDep,
    status_filter: OrderStatus | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[MerchantOrderResponse]:
    return service.list_merchant_orders(db, access.store.id, status_filter, offset, limit)


@router.get("/stores/{store_id}/orders/{order_id}", response_model=MerchantOrderResponse)
def get_order(order_id: int, db: SessionDep, access: OrdersReadDep) -> MerchantOrderResponse:
    return service.get_merchant_order(db, access.store.id, order_id)


@router.patch(
    "/stores/{store_id}/orders/{order_id}/status",
    response_model=MerchantOrderResponse,
    dependencies=[Depends(require_csrf)],
)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: SessionDep,
    access: OrdersFulfillDep,
) -> MerchantOrderResponse:
    return service.update_order_status(
        db, access.store.id, order_id, payload.status, access.principal.user.id
    )


@router.get("/stores/{store_id}/customers", response_model=list[CustomerResponse])
def list_customers(
    db: SessionDep,
    access: OrdersReadDep,
    q: str | None = Query(default=None, max_length=100),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[Customer]:
    query = select(Customer).where(Customer.store_id == access.store.id)
    if q:
        query = query.where(Customer.email.icontains(q, autoescape=True))
    return list(
        db.scalars(query.order_by(Customer.created_at.desc()).offset(offset).limit(limit)).all()
    )
