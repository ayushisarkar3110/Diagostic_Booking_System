from pydantic import BaseModel, EmailStr, Field
from typing import Literal
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)

class CentreCreate(BaseModel):
    name: str
    location: str


class TestCreate(BaseModel):
    name: str
    price: int = Field(gt=0)
    centre_id: int

class BookingCreate(BaseModel):
    test_id: int
    centre_id: int
    appointment_datetime: datetime

class PaymentCreate(BaseModel):
    booking_id: int
    outcome: Literal["SUCCESS", "FAILED"]


class PaymentWebhook(BaseModel):
    event_id: str
    booking_id: int
    outcome: Literal["SUCCESS", "FAILED"]