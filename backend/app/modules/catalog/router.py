from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select

from app.common.exceptions import DomainError
from app.core.rate_limit import rate_limit
from app.db.dependencies import SessionDep
from app.integrations.storage import s3
from app.modules.auth.dependencies import require_csrf
from app.modules.catalog import service
from app.modules.catalog.media_service import upload_product_media
from app.modules.catalog.models import Category, Product, ProductMedia, ProductVariant
from app.modules.catalog.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    ProductCreate,
    ProductDetail,
    ProductMediaResponse,
    ProductResponse,
    ProductStatus,
    ProductUpdate,
    VariantCreate,
    VariantResponse,
    VariantUpdate,
)
from app.modules.memberships.authorization import CatalogReadDep, CatalogWriteDep

router = APIRouter(prefix="/stores/{store_id}", tags=["catalog"])


def to_variant_response(variant: ProductVariant) -> VariantResponse:
    return VariantResponse.model_validate(variant)


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(access: CatalogReadDep, db: SessionDep) -> list[Category]:
    return service.list_categories(db, access.store.id)


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
def create_category(payload: CategoryCreate, db: SessionDep, access: CatalogWriteDep) -> Category:
    return service.create_category(db, access.store.id, payload)


@router.patch(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    dependencies=[Depends(require_csrf)],
)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: SessionDep,
    access: CatalogWriteDep,
) -> Category:
    return service.update_category(db, access.store.id, category_id, payload)


@router.get("/products", response_model=list[ProductResponse])
def list_products(
    db: SessionDep,
    access: CatalogReadDep,
    status_filter: ProductStatus | None = None,
    category_id: int | None = None,
    q: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[Product]:
    if offset < 0 or limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail="Invalid pagination")
    return service.list_products(db, access.store.id, status_filter, category_id, q, offset, limit)


@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
def create_product(
    payload: ProductCreate,
    db: SessionDep,
    access: CatalogWriteDep,
) -> Product:
    return service.create_product(db, access.store.id, payload)


@router.get("/products/{product_id}", response_model=ProductDetail)
def get_product(product_id: int, db: SessionDep, access: CatalogReadDep) -> ProductDetail:
    product, variants, media = service.product_detail(db, access.store.id, product_id)
    return ProductDetail(
        **ProductResponse.model_validate(product).model_dump(),
        variants=[to_variant_response(variant) for variant in variants],
        media=[ProductMediaResponse.model_validate(item) for item in media],
    )


@router.patch(
    "/products/{product_id}",
    response_model=ProductResponse,
    dependencies=[Depends(require_csrf)],
)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: SessionDep,
    access: CatalogWriteDep,
) -> Product:
    return service.update_product(db, access.store.id, product_id, payload)


@router.post(
    "/products/{product_id}/variants",
    response_model=VariantResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
def create_variant(
    product_id: int,
    payload: VariantCreate,
    db: SessionDep,
    access: CatalogWriteDep,
) -> VariantResponse:
    return to_variant_response(service.create_variant(db, access.store.id, product_id, payload))


@router.patch(
    "/products/{product_id}/variants/{variant_id}",
    response_model=VariantResponse,
    dependencies=[Depends(require_csrf)],
)
def update_variant(
    product_id: int,
    variant_id: int,
    payload: VariantUpdate,
    db: SessionDep,
    access: CatalogWriteDep,
) -> VariantResponse:
    return to_variant_response(
        service.update_variant(db, access.store.id, product_id, variant_id, payload)
    )


@router.post(
    "/products/{product_id}/media",
    response_model=ProductMediaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf), Depends(rate_limit("image-upload", 30, 3600))],
)
def upload_product_image(
    product_id: int,
    db: SessionDep,
    access: CatalogWriteDep,
    file: UploadFile = File(...),  # noqa: B008
    alt_text: str = Form(default="", max_length=250),
) -> ProductMediaResponse:
    service.get_product(db, access.store.id, product_id)
    content = file.file.read(s3.MAX_IMAGE_BYTES + 1)
    if len(content) > s3.MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the 8 MiB limit")
    try:
        content_type, extension = s3.detect_image_type(content)
    except ValueError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    image = upload_product_media(
        db,
        access.store.id,
        product_id,
        access.principal.user.id,
        content,
        content_type,
        extension,
        alt_text,
    )
    return ProductMediaResponse.model_validate(image)


@router.get("/products/{product_id}/media/{media_id}/url")
def get_product_image_url(
    product_id: int,
    media_id: int,
    db: SessionDep,
    access: CatalogReadDep,
) -> dict[str, str | int]:
    service.get_product(db, access.store.id, product_id)
    media = db.scalar(
        select(ProductMedia).where(
            ProductMedia.store_id == access.store.id,
            ProductMedia.product_id == product_id,
            ProductMedia.id == media_id,
        )
    )
    if media is None:
        raise DomainError(404, "Product image not found")
    try:
        url = s3.presigned_get_url(media.object_key)
    except s3.StorageError as exc:
        raise DomainError(503, str(exc)) from exc
    return {"url": url, "expires_in": 900}
