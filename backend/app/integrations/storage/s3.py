from typing import Any
from uuid import uuid4

import boto3  # type: ignore[import-untyped]
from botocore.exceptions import BotoCoreError, ClientError  # type: ignore[import-untyped]

from app.core.config import get_settings

MAX_IMAGE_BYTES = 8 * 1024 * 1024
_IMAGE_TYPES = {
    b"\xff\xd8\xff": ("image/jpeg", "jpg"),
    b"\x89PNG\r\n\x1a\n": ("image/png", "png"),
}


class StorageError(Exception):
    pass


def detect_image_type(content: bytes) -> tuple[str, str]:
    for signature, result in _IMAGE_TYPES.items():
        if content.startswith(signature):
            return result
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp", "webp"
    raise ValueError("Only JPEG, PNG, or WebP images are accepted")


def _client() -> Any:
    settings = get_settings()
    if not settings.s3_bucket:
        raise StorageError("Product image storage is not configured")
    return boto3.client(
        "s3",
        region_name=settings.s3_region,
        endpoint_url=settings.s3_endpoint_url,
    )


def upload_image(
    store_id: int, product_id: int, content: bytes, content_type: str, extension: str
) -> str:
    settings = get_settings()
    key = f"stores/{store_id}/products/{product_id}/{uuid4().hex}.{extension}"
    try:
        _client().put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=content,
            ContentType=content_type,
        )
    except (BotoCoreError, ClientError, StorageError) as exc:
        raise StorageError("Image upload failed") from exc
    return key


def delete_object(key: str) -> None:
    settings = get_settings()
    try:
        _client().delete_object(Bucket=settings.s3_bucket, Key=key)
    except (BotoCoreError, ClientError, StorageError) as exc:
        raise StorageError("Image cleanup failed") from exc


def presigned_get_url(key: str, expires_seconds: int = 900) -> str:
    settings = get_settings()
    try:
        return str(
            _client().generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.s3_bucket, "Key": key},
                ExpiresIn=expires_seconds,
            )
        )
    except (BotoCoreError, ClientError, StorageError) as exc:
        raise StorageError("Image URL generation failed") from exc
