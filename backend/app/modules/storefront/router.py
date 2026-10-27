from fastapi import APIRouter, Depends, Header, Query, status

from app.core.rate_limit import rate_limit
from app.db.dependencies import SessionDep
from app.modules.orders import service as order_service
from app.modules.orders.schemas import CheckoutRequest, CheckoutResponse, PublicOrderResponse
from app.modules.storefront import service
from app.modules.storefront.schemas import (
    PublicCategoryResponse,
    PublicProductResponse,
    PublicStoreResponse,
)

router = APIRouter(prefix="/public/stores/{store_slug}", tags=["public storefront"])
directory_router = APIRouter(prefix="/public", tags=["public storefront"])


@directory_router.get("/stores", response_model=list[PublicStoreResponse])
def list_public_stores(db: SessionDep) -> list[PublicStoreResponse]:
    return service.list_public_stores(db)


@router.get("", response_model=PublicStoreResponse)
def get_storefront(store_slug: str, db: SessionDep) -> PublicStoreResponse:
    return service.store_response(service.get_public_store(db, store_slug))


@router.get("/categories", response_model=list[PublicCategoryResponse])
def list_storefront_categories(store_slug: str, db: SessionDep) -> list[PublicCategoryResponse]:
    store = service.get_public_store(db, store_slug)
    return service.list_public_categories(db, store)


@router.get("/products", response_model=list[PublicProductResponse])
def list_storefront_products(
    store_slug: str,
    db: SessionDep,
    q: str | None = Query(default=None, max_length=100),
    category_id: int | None = Query(default=None, gt=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[PublicProductResponse]:
    store = service.get_public_store(db, store_slug)
    return service.list_public_products(db, store, q, category_id, limit)


@router.get("/products/{product_id}", response_model=PublicProductResponse)
def get_storefront_product(
    store_slug: str, product_id: int, db: SessionDep
) -> PublicProductResponse:
    store = service.get_public_store(db, store_slug)
    return service.get_public_product(db, store, product_id)


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("checkout", 8, 3600))],
)
def checkout(
    store_slug: str,
    payload: CheckoutRequest,
    db: SessionDep,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=16, max_length=128),
) -> CheckoutResponse:
    return order_service.create_cod_order(db, store_slug, idempotency_key, payload)


@router.get(
    "/orders/{order_code}",
    response_model=PublicOrderResponse,
    dependencies=[Depends(rate_limit("order-tracking", 30, 900))],
)
def track_order(
    store_slug: str,
    order_code: str,
    db: SessionDep,
    tracking_token: str = Header(alias="X-Order-Tracking-Token", min_length=32, max_length=128),
) -> PublicOrderResponse:
    return order_service.public_order(db, store_slug, order_code, tracking_token)
