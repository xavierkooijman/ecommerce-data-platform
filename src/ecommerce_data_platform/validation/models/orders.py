from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


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