import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

OrderStatus = Literal["pending", "confirmed", "shipped", "delivered", "cancelled"]


class CheckoutLine(BaseModel):
    variant_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=20)


class CheckoutRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    full_name: str = Field(min_length=2, max_length=160)
    phone: str = Field(min_length=7, max_length=32)
    shipping_address: str = Field(min_length=8, max_length=1000)
    city: str = Field(min_length=2, max_length=100)
    postal_code: str | None = Field(default=None, max_length=24)
    country: str = Field(default="BD", min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")
    items: list[CheckoutLine] = Field(min_length=1, max_length=20)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^@\s]{1,64}@[^@\s.]+(?:\.[^@\s.]+)+", value):
            raise ValueError("Enter a valid email address")
        return value

    @field_validator("full_name", "shipping_address", "city")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(r"[+0-9()\-\s]{7,32}", value):
            raise ValueError("Enter a valid phone number")
        return value

    @field_validator("postal_code")
    @classmethod
    def normalize_postal_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class CheckoutResponseItem(BaseModel):
    product_title: str
    variant_title: str
    sku: str
    quantity: int
    unit_price_minor: int
    line_total_minor: int


class CheckoutResponse(BaseModel):
    order_code: str
    status: OrderStatus
    payment_method: Literal["cash_on_delivery"]
    payment_status: Literal["unpaid", "paid"]
    subtotal_minor: int
    shipping_minor: int
    total_minor: int
    currency: str
    tracking_token: str
    items: list[CheckoutResponseItem]


class PublicOrderResponse(BaseModel):
    order_code: str
    status: OrderStatus
    payment_method: Literal["cash_on_delivery"]
    payment_status: Literal["unpaid", "paid"]
    total_minor: int
    currency: str
    created_at: datetime
    items: list[CheckoutResponseItem]


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class MerchantOrderResponse(PublicOrderResponse):
    id: int
    customer_id: int
    customer_email: str
    customer_name: str
    shipping_name: str
    shipping_phone: str
    shipping_address: str
    shipping_city: str
    shipping_postal_code: str | None
    shipping_country: str
