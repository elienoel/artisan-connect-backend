import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.availability import Availability
from app.models.professional import ProfessionalProfile
from app.models.user import User
from app.schemas.availability import AvailabilitySlotInput, AvailabilitySlotRead

router = APIRouter(tags=["availability"])


@router.get(
    "/professionals/{professional_id}/availability",
    response_model=list[AvailabilitySlotRead],
    summary="Get a professional's declared weekly working hours",
)
def get_availability(professional_id: uuid.UUID, db: Session = Depends(get_db)):
    if not db.get(ProfessionalProfile, professional_id):
        raise HTTPException(status_code=404, detail="Professional not found")
    return (
        db.query(Availability)
        .filter(Availability.professional_id == professional_id)
        .order_by(Availability.day_of_week, Availability.start_time)
        .all()
    )


@router.put(
    "/professionals/me/availability",
    response_model=list[AvailabilitySlotRead],
    summary="Replace the current professional's weekly working hours",
)
def set_my_availability(
    payload: list[AvailabilitySlotInput],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(ProfessionalProfile).filter(ProfessionalProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No professional profile for this user")

    seen: set[tuple[int, object]] = set()
    for slot in payload:
        key = (slot.day_of_week, slot.start_time)
        if key in seen:
            raise HTTPException(status_code=400, detail="Duplicate slot for the same day and start time")
        seen.add(key)

    db.query(Availability).filter(Availability.professional_id == profile.id).delete()
    rows = [
        Availability(
            professional_id=profile.id,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time,
            end_time=slot.end_time,
        )
        for slot in payload
    ]
    db.add_all(rows)
    db.commit()

    return (
        db.query(Availability)
        .filter(Availability.professional_id == profile.id)
        .order_by(Availability.day_of_week, Availability.start_time)
        .all()
    )
