import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProfessionalServiceBase(BaseModel):
    name: str = Field(..., max_length=150, examples=["Changement de robinet", "5 vetements"])
    unit: str | None = Field(None, max_length=60, examples=["intervention", "vetement"])
    price: float = Field(..., ge=0)
    currency: str = Field("FCFA", max_length=10)


class ProfessionalServiceCreate(ProfessionalServiceBase):
    position: int = 0


class ProfessionalServiceUpdate(BaseModel):
    name: str | None = Field(None, max_length=150)
    unit: str | None = Field(None, max_length=60)
    price: float | None = Field(None, ge=0)
    currency: str | None = Field(None, max_length=10)
    position: int | None = None
    is_active: bool | None = None


class ProfessionalServiceRead(ProfessionalServiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    professional_id: uuid.UUID
    position: int
    is_active: bool
    created_at: datetime
