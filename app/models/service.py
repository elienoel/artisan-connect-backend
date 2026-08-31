import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProfessionalService(Base):
    """A priced prestation defined by a professional, e.g. 'Changement de robinet'
    at 3000 XOF, or '5 vetements' at 2000 XOF for a dry cleaner. Each professional
    freely defines their own list of prestations, units and unit prices."""

    __tablename__ = "professional_services"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professional_profiles.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(60), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="FCFA")

    position: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    professional: Mapped["ProfessionalProfile"] = relationship("ProfessionalProfile", back_populates="services")
