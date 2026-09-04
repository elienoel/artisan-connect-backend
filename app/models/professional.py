import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class VerificationStatus(str, enum.Enum):
    UNSUBMITTED = "unsubmitted"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class SubscriptionPlan(str, enum.Enum):
    FREE = "free"
    PREMIUM = "premium"


class ProfessionalProfile(Base):
    __tablename__ = "professional_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    profession_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professions.id"), nullable=False
    )

    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    hourly_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    rating_avg: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    is_verified: Mapped[bool] = mapped_column(default=False)

    # Identity verification workflow (KYC): a professional submits an ID
    # document, an admin approves or rejects it. `is_verified` above stays in
    # sync (True only while status == VERIFIED) since it's the public signal
    # shown to clients; these fields carry the detail needed by the owner and
    # by admins reviewing the queue.
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status"),
        default=VerificationStatus.UNSUBMITTED,
        nullable=False,
    )
    verification_document_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    verification_document_object_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    verification_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Monetization (section 7 of the business plan): a paid subscription for
    # extra features, and a paid search-ranking boost. Payments themselves
    # are simulated for now (see app/services/payment_gateway.py) — these
    # fields track the resulting entitlement regardless of which real
    # provider eventually issues the charge.
    subscription_plan: Mapped[SubscriptionPlan] = mapped_column(
        Enum(SubscriptionPlan, name="subscription_plan"), default=SubscriptionPlan.FREE, nullable=False
    )
    subscription_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_boosted: Mapped[bool] = mapped_column(default=False)
    boosted_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="professional_profile")
    profession: Mapped["Profession"] = relationship("Profession", back_populates="professionals")
    media: Mapped[list["Media"]] = relationship(
        "Media", back_populates="professional", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["Review"]] = relationship(
        "Review", back_populates="professional", cascade="all, delete-orphan"
    )
    services: Mapped[list["ProfessionalService"]] = relationship(
        "ProfessionalService",
        back_populates="professional",
        cascade="all, delete-orphan",
        order_by="ProfessionalService.position",
    )

    @property
    def is_premium_active(self) -> bool:
        return (
            self.subscription_plan == SubscriptionPlan.PREMIUM
            and self.subscription_expires_at is not None
            and self.subscription_expires_at > datetime.now(timezone.utc)
        )

    @property
    def is_boost_active(self) -> bool:
        return self.is_boosted and self.boosted_until is not None and self.boosted_until > datetime.now(timezone.utc)
