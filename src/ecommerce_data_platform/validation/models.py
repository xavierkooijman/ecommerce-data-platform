from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field


class Customer(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    country : str
    city: str | None
    is_active: bool
    signup_date: date
    created_at: datetime
    updated_at: datetime

class Product(BaseModel):
    id: int
    sku: str
    name: str
    category: str
    price: Decimal = Field(ge=0)
    created_at: datetime
    updated_at: datetime

class OrderStatus(StrEnum):
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"

class PaymentMethod(StrEnum):
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    BANK_TRANSFER = "bank_transfer"
    GOOGLE_PAY = "google_pay"

class Order(BaseModel):
    id: int
    customer_id: int
    status: OrderStatus
    payment_method: PaymentMethod
    order_date: datetime
    created_at: datetime
    updated_at: datetime

class OrderItem(BaseModel):
    id: int
    order_id: int
    product_id: int
    quantity: int = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    created_at: datetime
    updated_at: datetime

class Shipment(BaseModel):
    id: int
    order_id: int
    carrier: str
    shipped_at: datetime | None
    delivered_at: datetime | None
    created_at: datetime
    updated_at: datetime