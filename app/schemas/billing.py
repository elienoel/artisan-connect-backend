import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.payment import PaymentPurpose, PaymentStatus
from app.models.professional import SubscriptionPlan


class SubscribeRequest(BaseModel):
    plan: Literal["premium"] = "premium"


class BoostRequest(BaseModel):
    days: int = Field(..., ge=1, le=90)


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    purpose: PaymentPurpose
    status: PaymentStatus
    amount: float
    currency: str
    created_at: datetime
    paid_at: datetime | None


class BillingStatusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    subscription_plan: SubscriptionPlan
    subscription_expires_at: datetime | None
    is_premium_active: bool
    boosted_until: datetime | None
    is_boost_active: bool
