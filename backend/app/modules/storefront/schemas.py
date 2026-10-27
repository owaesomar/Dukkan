from pydantic import BaseModel


class PublicStoreResponse(BaseModel):
    id: int
    slug: str
    name: str


class PublicCategoryResponse(BaseModel):
    id: int
    name: str
    slug: str


class PublicVariantResponse(BaseModel):
    id: int
    sku: str
    title: str
    price_minor: int
    currency: str
    options: dict[str, str]
    available_quantity: int


class PublicMediaResponse(BaseModel):
    id: int
    alt_text: str
    position: int
    image_url: str | None


class PublicProductResponse(BaseModel):
    id: int
    title: str
    description: str | None
    category_id: int | None
    variants: list[PublicVariantResponse]
    media: list[PublicMediaResponse]
