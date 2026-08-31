import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.media import MediaType


class MediaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    professional_id: uuid.UUID
    url: str
    media_type: MediaType
    created_at: datetime
