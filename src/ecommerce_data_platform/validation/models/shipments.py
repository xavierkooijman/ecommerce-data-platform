from datetime import datetime

from pydantic import BaseModel


class Customer(BaseModel):
    id: int
    order_id: int
    carrier: str
    shipped_date: datetime | None
    delivered_at: datetime | None
    created_at: datetime
    updated_at: datetime