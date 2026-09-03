import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.booking import Booking, BookingStatus
from app.models.professional import ProfessionalProfile
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewRead
from app.models.user import User

router = APIRouter(prefix="/bookings", tags=["reviews"])


@router.post(
    "/{booking_id}/review", response_model=ReviewRead, status_code=201, summary="Leave a review on a completed booking"
)
def create_review(
    booking_id: uuid.UUID,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Only the client of this booking can leave a review
    if booking.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the client can review this booking")

    # Booking must be completed
    if booking.status != BookingStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Can only review a completed booking")

    # One review per booking
    existing = db.query(Review).filter(Review.booking_id == booking_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="This booking has already been reviewed")

    profile = db.get(ProfessionalProfile, booking.professional_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Professional not found")

    review = Review(
        booking_id=booking_id,
        professional_id=booking.professional_id,
        client_id=current_user.id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(review)
    db.flush()

    # Recalculate rating_avg and rating_count on the professional profile
    result = db.query(
        func.avg(Review.rating).label("avg"),
        func.count(Review.id).label("count"),
    ).filter(Review.professional_id == profile.id).one()

    profile.rating_avg = round(float(result.avg or 0), 2)
    profile.rating_count = result.count

    db.commit()
    db.refresh(review)
    return review

