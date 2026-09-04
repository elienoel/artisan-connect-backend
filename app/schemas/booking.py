import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.booking import BookingStatus
from app.schemas.review import ReviewRead


class BookingItemCreate(BaseModel):
    service_id: uuid.UUID
    quantity: int = Field(1, ge=1, le=1000)


class BookingItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service_id: uuid.UUID | None
    service_name: str
    unit: str | None
    unit_price: float
    quantity: int
    subtotal: float


class BookingCreate(BaseModel):
    professional_id: uuid.UUID
    items: list[BookingItemCreate] = Field(..., min_length=1)
    address: str = Field(..., max_length=500)
    latitude: float
    longitude: float
    scheduled_at: datetime
    notes: str | None = None


class BookingStatusUpdate(BaseModel):
    status: BookingStatus


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    client_id: uuid.UUID
    professional_id: uuid.UUID
    status: BookingStatus
    address: str
    latitude: float
    longitude: float
    scheduled_at: datetime | None
    notes: str | None
    total_price: float
    currency: str
    created_at: datetime
    updated_at: datetime
    items: list[BookingItemRead] = []
    review: ReviewRead | None = None

