import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.professional import VerificationStatus
from app.schemas.user import UserRead


class VerificationDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    verification_status: VerificationStatus
    verification_document_url: str | None
    verification_submitted_at: datetime | None
    verification_reviewed_at: datetime | None
    verification_rejection_reason: str | None


class VerificationQueueItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_name: str
    verification_status: VerificationStatus
    verification_document_url: str | None
    verification_submitted_at: datetime | None
    user: UserRead


class VerificationReject(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)
