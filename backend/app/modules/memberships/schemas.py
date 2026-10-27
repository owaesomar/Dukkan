from datetime import datetime
from typing import Literal

from pydantic import BaseModel

MembershipRole = Literal["owner", "admin", "manager", "catalog", "fulfillment", "staff", "viewer"]
AssignableRole = Literal["admin", "manager", "catalog", "fulfillment", "staff", "viewer"]


class MembershipCreate(BaseModel):
    email: str
    role: AssignableRole


class MembershipUpdate(BaseModel):
    role: MembershipRole


class MembershipResponse(BaseModel):
    store_id: int
    user_id: int
    email: str
    role: MembershipRole
    is_active: bool
    created_at: datetime
