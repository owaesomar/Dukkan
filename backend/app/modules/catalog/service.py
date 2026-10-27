from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.exceptions import DomainError
from app.modules.catalog.models import Category, Product, ProductMedia, ProductVariant
from app.modules.catalog.schemas import (
    CategoryCreate,
    CategoryUpdate,
    ProductCreate,
    ProductUpdate,
    VariantCreate,
    VariantUpdate,
)
from app.modules.inventory.models import Inventory


def _get_category(db: Session, store_id: int, category_id: int) -> Category:
    category = db.scalar(
        select(Category).where(Category.store_id == store_id, Category.id == category_id)
    )
    if category is None:
        raise DomainError(404, "Category not found")
    return category


def _get_product(db: Session, store_id: int, product_id: int) -> Product:
    product = db.scalar(
        select(Product).where(Product.store_id == store_id, Product.id == product_id)
    )
    if product is None:
        raise DomainError(404, "Product not found")
    return product


def create_category(db: Session, store_id: int, payload: CategoryCreate) -> Category:
    if payload.parent_id is not None:
        _get_category(db, store_id, payload.parent_id)
    category = Category(store_id=store_id, **payload.model_dump())
    db.add(category)
    try:
        db.commit()
        db.refresh(category)
    except IntegrityError as exc:
        db.rollback()
        raise DomainError(409, "Category slug is already in use in this store") from exc
    return category


def list_categories(db: Session, store_id: int) -> list[Category]:
    return list(
        db.scalars(
            select(Category)
            .where(Category.store_id == store_id)
            .order_by(Category.name, Category.id)
        ).all()
    )


def update_category(
    db: Session, store_id: int, category_id: int, payload: CategoryUpdate
) -> Category:
    category = _get_category(db, store_id, category_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, key, value)
    try:
        db.commit()
        db.refresh(category)
    except IntegrityError as exc:
        db.rollback()
        raise DomainError(409, "Category slug is already in use in this store") from exc
    return category


def create_product(db: Session, store_id: int, payload: ProductCreate) -> Product:
    if payload.category_id is not None:
        _get_category(db, store_id, payload.category_id)
    product = Product(store_id=store_id, **payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def list_products(
    db: Session,
    store_id: int,
    status_filter: str | None,
    category_id: int | None,
    search: str | None,
    offset: int,
    limit: int,
) -> list[Product]:
    query = select(Product).where(Product.store_id == store_id)
    if status_filter is not None:
        query = query.where(Product.status == status_filter)
    if category_id is not None:
        query = query.where(Product.category_id == category_id)
    if search:
        query = query.where(Product.title.icontains(search, autoescape=True))
    return list(db.scalars(query.order_by(Product.id.desc()).offset(offset).limit(limit)).all())


def get_product(db: Session, store_id: int, product_id: int) -> Product:
    return _get_product(db, store_id, product_id)


def update_product(db: Session, store_id: int, product_id: int, payload: ProductUpdate) -> Product:
    product = _get_product(db, store_id, product_id)
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("category_id") is not None:
        _get_category(db, store_id, changes["category_id"])
    if changes.get("status") == "published":
        variant_count = db.scalar(
            select(ProductVariant.id)
            .where(
                ProductVariant.store_id == store_id,
                ProductVariant.product_id == product_id,
                ProductVariant.is_active.is_(True),
            )
            .limit(1)
        )
        if variant_count is None:
            raise DomainError(422, "Add an active variant before publishing this product")
    for key, value in changes.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


def product_detail(
    db: Session, store_id: int, product_id: int
) -> tuple[Product, list[ProductVariant], list[ProductMedia]]:
    product = _get_product(db, store_id, product_id)
    variants = list(
        db.scalars(
            select(ProductVariant)
            .where(ProductVariant.store_id == store_id, ProductVariant.product_id == product_id)
            .order_by(ProductVariant.id)
        ).all()
    )
    inventory_rows = (
        db.scalars(
            select(Inventory).where(
                Inventory.store_id == store_id,
                Inventory.variant_id.in_([variant.id for variant in variants]),
            )
        ).all()
        if variants
        else []
    )
    inventory_by_variant = {item.variant_id: item for item in inventory_rows}
    for variant in variants:
        inventory = inventory_by_variant.get(variant.id)
        variant.quantity_on_hand = inventory.quantity_on_hand if inventory else 0  # type: ignore[attr-defined]
        variant.reserved_quantity = inventory.reserved_quantity if inventory else 0  # type: ignore[attr-defined]
    media = list(
        db.scalars(
            select(ProductMedia)
            .where(ProductMedia.store_id == store_id, ProductMedia.product_id == product_id)
            .order_by(ProductMedia.position, ProductMedia.id)
        ).all()
    )
    return product, variants, media


def create_variant(
    db: Session, store_id: int, product_id: int, payload: VariantCreate
) -> ProductVariant:
    _get_product(db, store_id, product_id)
    variant = ProductVariant(
        store_id=store_id,
        product_id=product_id,
        sku=payload.sku,
        title=payload.title,
        price_minor=payload.price_minor,
        currency=payload.currency,
        options=payload.options,
    )
    db.add(variant)
    try:
        db.flush()
        db.add(Inventory(store_id=store_id, variant_id=variant.id, quantity_on_hand=0))
        db.commit()
        db.refresh(variant)
    except IntegrityError as exc:
        db.rollback()
        raise DomainError(409, "SKU is already in use in this store") from exc
    variant.quantity_on_hand = 0  # type: ignore[attr-defined]
    variant.reserved_quantity = 0  # type: ignore[attr-defined]
    return variant


def update_variant(
    db: Session,
    store_id: int,
    product_id: int,
    variant_id: int,
    payload: VariantUpdate,
) -> ProductVariant:
    _get_product(db, store_id, product_id)
    variant = db.scalar(
        select(ProductVariant).where(
            ProductVariant.store_id == store_id,
            ProductVariant.product_id == product_id,
            ProductVariant.id == variant_id,
        )
    )
    if variant is None:
        raise DomainError(404, "Variant not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is None:
            raise DomainError(422, "Variant fields cannot be null")
        setattr(variant, key, value)
    try:
        db.commit()
        db.refresh(variant)
    except IntegrityError as exc:
        db.rollback()
        raise DomainError(409, "SKU is already in use in this store") from exc
    inventory = db.get(Inventory, (store_id, variant.id))
    variant.quantity_on_hand = inventory.quantity_on_hand if inventory else 0  # type: ignore[attr-defined]
    variant.reserved_quantity = inventory.reserved_quantity if inventory else 0  # type: ignore[attr-defined]
    return variant
