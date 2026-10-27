import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.common.exceptions import DomainError
from app.integrations.storage import s3
from app.modules.catalog.models import ProductMedia
from app.modules.catalog.service import get_product

logger = logging.getLogger(__name__)


def upload_product_media(
    db: Session,
    store_id: int,
    product_id: int,
    uploaded_by_user_id: int,
    content: bytes,
    content_type: str,
    extension: str,
    alt_text: str,
) -> ProductMedia:
    get_product(db, store_id, product_id)
    existing_position = db.scalar(
        select(ProductMedia.position)
        .where(ProductMedia.store_id == store_id, ProductMedia.product_id == product_id)
        .order_by(ProductMedia.position.desc())
        .limit(1)
    )
    next_position = (existing_position or -1) + 1
    try:
        object_key = s3.upload_image(store_id, product_id, content, content_type, extension)
    except s3.StorageError as exc:
        raise DomainError(503, str(exc)) from exc
    media = ProductMedia(
        store_id=store_id,
        product_id=product_id,
        object_key=object_key,
        uploaded_by_user_id=uploaded_by_user_id,
        content_type=content_type,
        byte_size=len(content),
        alt_text=alt_text.strip(),
        position=next_position,
    )
    db.add(media)
    try:
        db.commit()
        db.refresh(media)
    except SQLAlchemyError:
        db.rollback()
        try:
            s3.delete_object(object_key)
        except s3.StorageError:
            logger.exception("Could not remove orphaned product media object %s", object_key)
        raise
    return media
