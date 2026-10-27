from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StoreCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(
        min_length=3,
        max_length=63,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Store name cannot be blank")
        return normalized


class StoreUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    slug: str | None = Field(
        default=None,
        min_length=3,
        max_length=63,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Store name cannot be blank")
        return normalized

    @model_validator(mode="after")
    def reject_null_values(self) -> "StoreUpdate":
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Store fields cannot be null")
        return self


class StoreResponse(BaseModel):
    id: int
    name: str
    slug: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
