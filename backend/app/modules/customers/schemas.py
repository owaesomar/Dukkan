from datetime import datetime

from pydantic import BaseModel


class CustomerResponse(BaseModel):
    id: int
    store_id: int
    email: str
    full_name: str
    phone: str
    created_at: datetime
