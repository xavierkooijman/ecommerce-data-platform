from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class OrderItem(BaseModel):
    id: int
    order_id: int
    product_id: int
    quantity: int = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    created_at: datetime
    updated_at: datetime