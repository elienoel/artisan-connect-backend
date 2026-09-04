import uuid
from datetime import time

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AvailabilitySlotInput(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="0 = Monday ... 6 = Sunday")
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def _check_range(self) -> "AvailabilitySlotInput":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class AvailabilitySlotRead(AvailabilitySlotInput):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
