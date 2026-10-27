from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

BillingInterval = Literal["monthly", "yearly"]
SubscriptionStatus = Literal["active", "past_due", "canceled"]


class PlanCreate(BaseModel):
    code: str = Field(min_length=2, max_length=40, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price_minor: int = Field(ge=0, le=2_000_000_000)
    currency: str = Field(default="BDT", pattern=r"^[A-Z]{3}$")
    billing_interval: BillingInterval = "monthly"
    limits: dict[str, int] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Plan name cannot be blank")
        return value

    @field_validator("limits")
    @classmethod
    def validate_limits(cls, value: dict[str, int]) -> dict[str, int]:
        if any(not key or len(key) > 40 or limit < 0 for key, limit in value.items()):
            raise ValueError("Plan limits must have short names and nonnegative values")
        return value


class PlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price_minor: int | None = Field(default=None, ge=0, le=2_000_000_000)
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    billing_interval: BillingInterval | None = None
    limits: dict[str, int] | None = None
    is_active: bool | None = None


class PlanResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str | None
    price_minor: int
    currency: str
    billing_interval: BillingInterval
    limits: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubscriptionResponse(BaseModel):
    store_id: int
    plan: PlanResponse
    status: SubscriptionStatus
    cancellation_reason: str | None
    started_at: datetime
    current_period_end: datetime | None
    cancel_at_period_end: bool
    updated_at: datetime


class SubscriptionChange(BaseModel):
    plan_id: int = Field(gt=0)


class SubscriptionCancel(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class PlatformStoreResponse(BaseModel):
    id: int
    name: str
    slug: str
    status: Literal["active", "suspended", "disabled"]
    created_at: datetime
    owner_email: str | None
    members_count: int


class StoreStatusUpdate(BaseModel):
    status: Literal["active", "suspended", "disabled"]
    reason: str = Field(min_length=3, max_length=500)


class MerchantStatusUpdate(BaseModel):
    is_active: bool
    reason: str = Field(min_length=3, max_length=500)


class PlatformMerchantResponse(BaseModel):
    user_id: int
    email: str
    is_active: bool
    stores_count: int
    created_at: datetime


class PlatformOverview(BaseModel):
    users_count: int
    stores_count: int
    active_stores_count: int
    suspended_stores_count: int
    orders_count: int
    subscriptions_count: int
    monthly_recurring_revenue_by_currency: dict[str, int]


class PlatformAuditResponse(BaseModel):
    id: int
    actor_user_id: int
    action: str
    resource_type: str
    resource_id: str
    details: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlatformSubscriptionResponse(BaseModel):
    store_id: int
    store_name: str
    store_slug: str
    plan_id: int
    plan_code: str
    plan_name: str
    price_minor: int
    currency: str
    billing_interval: BillingInterval
    status: SubscriptionStatus
    cancellation_reason: str | None
    started_at: datetime
    current_period_end: datetime | None
    cancel_at_period_end: bool


class AdminGrantRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class AdminGrantResponse(BaseModel):
    user_id: int
    email: str
    is_active: bool
    created_at: datetime
