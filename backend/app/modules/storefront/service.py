import logging
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.exceptions import DomainError
from app.core.config import get_settings
from app.integrations.storage import s3
from app.modules.catalog.models import Category, Product, ProductMedia, ProductVariant
from app.modules.inventory.models import Inventory
from app.modules.storefront.schemas import (
    PublicCategoryResponse,
    PublicMediaResponse,
    PublicProductResponse,
    PublicStoreResponse,
    PublicVariantResponse,
)
from app.modules.stores.models import Store

logger = logging.getLogger(__name__)


def get_public_store(db: Session, slug: str) -> Store:
    store = db.scalar(select(Store).where(Store.slug == slug, Store.status == "active"))
    if store is None:
        raise DomainError(404, "Store not found")
    return store


def list_public_stores(db: Session) -> list[PublicStoreResponse]:
    stores = db.scalars(
        select(Store).where(Store.status == "active").order_by(Store.name, Store.id)
    ).all()
    return [store_response(store) for store in stores]


def store_response(store: Store) -> PublicStoreResponse:
    return PublicStoreResponse(id=store.id, slug=store.slug, name=store.name)


def list_public_categories(db: Session, store: Store) -> list[PublicCategoryResponse]:
    rows = db.scalars(
        select(Category)
        .join(
            Product,
            (Product.store_id == Category.store_id) & (Product.category_id == Category.id),
        )
        .join(
            ProductVariant,
            (ProductVariant.store_id == Product.store_id)
            & (ProductVariant.product_id == Product.id),
        )
        .join(
            Inventory,
            (Inventory.store_id == ProductVariant.store_id)
            & (Inventory.variant_id == ProductVariant.id),
        )
        .where(
            Category.store_id == store.id,
            Product.status == "published",
            ProductVariant.is_active.is_(True),
        )
        .distinct()
        .order_by(Category.name)
    ).all()
    return [PublicCategoryResponse(id=row.id, name=row.name, slug=row.slug) for row in rows]


def list_public_products(
    db: Session, store: Store, search: str | None, category_id: int | None, limit: int
) -> list[PublicProductResponse]:
    query = select(Product).where(Product.store_id == store.id, Product.status == "published")
    if search:
        query = query.where(Product.title.icontains(search, autoescape=True))
    if category_id is not None:
        query = query.where(Product.category_id == category_id)
    products = list(db.scalars(query.order_by(Product.id.desc()).limit(limit)).all())
    if not products:
        return []
    return _product_responses(db, store.id, products)


def get_public_product(db: Session, store: Store, product_id: int) -> PublicProductResponse:
    product = db.scalar(
        select(Product).where(
            Product.store_id == store.id,
            Product.id == product_id,
            Product.status == "published",
        )
    )
    if product is None:
        raise DomainError(404, "Product not found")
    return _product_responses(db, store.id, [product])[0]


def _product_responses(
    db: Session, store_id: int, products: list[Product]
) -> list[PublicProductResponse]:
    product_ids = [product.id for product in products]
    rows = db.execute(
        select(ProductVariant, Inventory)
        .join(
            Inventory,
            (Inventory.store_id == ProductVariant.store_id)
            & (Inventory.variant_id == ProductVariant.id),
        )
        .where(
            ProductVariant.store_id == store_id,
            ProductVariant.product_id.in_(product_ids),
            ProductVariant.is_active.is_(True),
        )
        .order_by(ProductVariant.id)
    ).all()
    variants_by_product: dict[int, list[PublicVariantResponse]] = defaultdict(list)
    for variant, inventory in rows:
        variants_by_product[variant.product_id].append(
            PublicVariantResponse(
                id=variant.id,
                sku=variant.sku,
                title=variant.title,
                price_minor=variant.price_minor,
                currency=variant.currency,
                options=variant.options,
                available_quantity=max(0, inventory.quantity_on_hand - inventory.reserved_quantity),
            )
        )

    media_by_product: dict[int, list[PublicMediaResponse]] = defaultdict(list)
    for media in db.scalars(
        select(ProductMedia)
        .where(ProductMedia.store_id == store_id, ProductMedia.product_id.in_(product_ids))
        .order_by(ProductMedia.position, ProductMedia.id)
    ).all():
        image_url: str | None = None
        if get_settings().s3_bucket:
            try:
                image_url = s3.presigned_get_url(media.object_key)
            except s3.StorageError:
                logger.warning(
                    "Could not create public product image URL", extra={"media_id": media.id}
                )
                image_url = None
        media_by_product[media.product_id].append(
            PublicMediaResponse(
                id=media.id,
                alt_text=media.alt_text,
                position=media.position,
                image_url=image_url,
            )
        )

    return [
        PublicProductResponse(
            id=product.id,
            title=product.title,
            description=product.description,
            category_id=product.category_id,
            variants=variants_by_product[product.id],
            media=media_by_product[product.id],
        )
        for product in products
        if variants_by_product[product.id]
    ]
