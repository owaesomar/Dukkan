from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ProductStatus = Literal["draft", "published", "archived"]


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=2, max_length=63, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = Field(default=None, max_length=1000)
    parent_id: int | None = Field(default=None, gt=0)

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Category name cannot be blank")
        return value


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    slug: str | None = Field(
        default=None, min_length=2, max_length=63, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    description: str | None = Field(default=None, max_length=1000)

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Category name cannot be blank")
        return value

    @model_validator(mode="after")
    def require_changes(self) -> "CategoryUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field is required")
        if any(getattr(self, field) is None for field in {"name", "slug"} & self.model_fields_set):
            raise ValueError("Category name and slug cannot be null")
        return self


class CategoryResponse(BaseModel):
    id: int
    store_id: int
    parent_id: int | None
    name: str
    slug: str
    description: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    category_id: int | None = Field(default=None, gt=0)

    @field_validator("title")
    @classmethod
    def trim_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Product title cannot be blank")
        return value


class ProductUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    category_id: int | None = Field(default=None, gt=0)
    status: ProductStatus | None = None

    @field_validator("title")
    @classmethod
    def trim_title(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Product title cannot be blank")
        return value

    @model_validator(mode="after")
    def reject_null_required_fields(self) -> "ProductUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field is required")
        if any(
            getattr(self, field) is None
            for field in {"title", "status"}.intersection(self.model_fields_set)
        ):
            raise ValueError("Product title and status cannot be null")
        return self


class VariantCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    title: str = Field(default="Default", min_length=1, max_length=100)
    price_minor: int = Field(ge=0, le=2_000_000_000)
    currency: str = Field(default="BDT", pattern=r"^[A-Z]{3}$")
    options: dict[str, str] = Field(default_factory=dict, max_length=20)

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("SKU cannot be blank")
        return value

    @field_validator("title")
    @classmethod
    def trim_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Variant title cannot be blank")
        return value

    @field_validator("options")
    @classmethod
    def validate_options(cls, value: dict[str, str]) -> dict[str, str]:
        if any(
            not key.strip() or len(key) > 50 or len(option) > 100 for key, option in value.items()
        ):
            raise ValueError("Variant options have invalid key or value lengths")
        return {key.strip(): option.strip() for key, option in value.items()}


class VariantUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=64)
    title: str | None = Field(default=None, min_length=1, max_length=100)
    price_minor: int | None = Field(default=None, ge=0, le=2_000_000_000)
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    options: dict[str, str] | None = Field(default=None, max_length=20)
    is_active: bool | None = None

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip().upper()
        if not value:
            raise ValueError("SKU cannot be blank")
        return value

    @field_validator("title")
    @classmethod
    def trim_title(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Variant title cannot be blank")
        return value

    @model_validator(mode="after")
    def require_changes(self) -> "VariantUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field is required")
        return self


class VariantResponse(BaseModel):
    id: int
    store_id: int
    product_id: int
    sku: str
    title: str
    price_minor: int
    currency: str
    options: dict[str, str]
    is_active: bool
    quantity_on_hand: int = 0
    reserved_quantity: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductResponse(BaseModel):
    id: int
    store_id: int
    category_id: int | None
    title: str
    description: str | None
    status: ProductStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductMediaResponse(BaseModel):
    id: int
    store_id: int
    product_id: int
    content_type: str
    byte_size: int
    alt_text: str
    position: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductDetail(ProductResponse):
    variants: list[VariantResponse]
    media: list[ProductMediaResponse]
