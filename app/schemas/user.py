import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.models.user import UserRole

_PHONE_RE = re.compile(r"^\+\d{8,15}$")


class UserBase(BaseModel):
    full_name: str
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    @field_validator("email", mode="before")
    @classmethod
    def blank_email_to_none(cls, value: str | None) -> str | None:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class UserCreate(UserBase):
    password: str
    phone: str
    role: UserRole = UserRole.CLIENT

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not _PHONE_RE.match(value):
            raise ValueError("Phone number must be in international format, e.g. +2250700000001")
        return value


class UserLogin(BaseModel):
    identifier: str  # email address or phone number
    password: str


class UserProfileUpdate(BaseModel):
    full_name: str | None = None
    address: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: UserRole
    avatar_url: str | None = None
    is_phone_verified: bool = False
    is_email_verified: bool = False
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
