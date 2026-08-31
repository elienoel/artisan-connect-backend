import uuid

from pydantic import BaseModel, ConfigDict


class ProfessionBase(BaseModel):
    name: str
    slug: str
    icon: str | None = None
    category: str | None = None


class ProfessionCreate(ProfessionBase):
    pass


class ProfessionRead(ProfessionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_active: bool
