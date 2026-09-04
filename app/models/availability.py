import uuid
from datetime import time

from sqlalchemy import ForeignKey, Integer, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Availability(Base):
    """A recurring weekly working-hours slot for a professional, e.g. Monday
    08:00-18:00. A professional with no rows here is treated as having no
    declared schedule, so booking requests aren't restricted to any slot."""

    __tablename__ = "availabilities"
    __table_args__ = (
        UniqueConstraint("professional_id", "day_of_week", "start_time", name="uq_availability_professional_slot"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    professional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professional_profiles.id", ondelete="CASCADE"), nullable=False
    )
    # 0 = Monday ... 6 = Sunday (Python's datetime.weekday() convention).
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
