import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.message import MessageType
from app.schemas.booking import BookingRead
from app.schemas.user import UserRead


class ConversationCreate(BaseModel):
    professional_user_id: uuid.UUID


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    content: str
    message_type: MessageType = MessageType.TEXT
    booking: BookingRead | None = None
    media_url: str | None = None
    media_mime_type: str | None = None
    media_duration_seconds: int | None = None
    created_at: datetime
    read_at: datetime | None = None


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    professional_id: uuid.UUID
    created_at: datetime
    other_user: UserRead | None = None
    last_message: MessageRead | None = None


class WSMessageIn(BaseModel):
    content: str


class WSMessageOut(BaseModel):
    type: str = "message"
    message: MessageRead
