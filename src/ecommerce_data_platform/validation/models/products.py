from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class Product(BaseModel):
    id: int
    sku: str
    name: str
    category: str
    price: Decimal = Field(ge=0)
    created_at: datetime
    updated_at: datetime