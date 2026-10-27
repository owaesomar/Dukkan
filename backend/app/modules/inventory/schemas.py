from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InventoryAdjustmentCreate(BaseModel):
    delta: int = Field(ge=-1_000_000, le=1_000_000)
    reason: str = Field(min_length=3, max_length=500)

    @field_validator("delta")
    @classmethod
    def nonzero_delta(cls, value: int) -> int:
        if value == 0:
            raise ValueError("Inventory adjustment cannot be zero")
        return value

    @field_validator("reason")
    @classmethod
    def trim_reason(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Provide an adjustment reason")
        return value


class InventoryAdjustmentResponse(BaseModel):
    id: int
    store_id: int
    variant_id: int
    actor_user_id: int
    delta: int
    reason: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryResponse(BaseModel):
    store_id: int
    variant_id: int
    sku: str
    product_id: int
    product_title: str
    quantity_on_hand: int
    reserved_quantity: int
    updated_at: datetime
