import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.profession import ProfessionRead
from app.schemas.service import ProfessionalServiceRead
from app.schemas.user import UserRead


class ProfessionalProfileBase(BaseModel):
    business_name: str
    description: str | None = None
    hourly_rate: float | None = None
    address: str | None = None
    city: str | None = None
    latitude: float
    longitude: float


class ProfessionalProfileCreate(ProfessionalProfileBase):
    profession_id: uuid.UUID


class ProfessionalProfileUpdate(BaseModel):
    business_name: str | None = None
    description: str | None = None
    hourly_rate: float | None = None
    address: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    profession_id: uuid.UUID | None = None


class ProfessionalProfileRead(ProfessionalProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rating_avg: float
    rating_count: int
    is_verified: bool
    created_at: datetime
    profession: ProfessionRead
    user: UserRead
    distance_km: float | None = None
    photo_urls: list[str] = []
    services: list[ProfessionalServiceRead] = []
    is_favorite: bool = False
    is_boost_active: bool = False
