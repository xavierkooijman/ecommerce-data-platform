from datetime import date, datetime

from pydantic import BaseModel, EmailStr


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