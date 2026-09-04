import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.availability import Availability
from app.models.booking import Booking, BookingItem, BookingStatus
from app.models.conversation import Conversation
from app.models.message import Message, MessageType
from app.models.professional import ProfessionalProfile
from app.models.service import ProfessionalService
from app.models.user import User, UserRole
from app.schemas.booking import BookingCreate, BookingRead, BookingStatusUpdate
from app.schemas.chat import MessageRead
from app.ws.manager import manager

router = APIRouter(prefix="/bookings", tags=["bookings"])

# A professional can only accept/decline a pending booking, then mark an
# accepted one completed or cancelled. Any other transition is rejected.
_ALLOWED_TRANSITIONS = {
    BookingStatus.PENDING: {BookingStatus.ACCEPTED, BookingStatus.DECLINED, BookingStatus.CANCELLED},
    BookingStatus.ACCEPTED: {BookingStatus.COMPLETED, BookingStatus.CANCELLED},
}


def _summary_text(items: list[BookingItem], total_price: float, currency: str) -> str:
    lines = [f"{item.quantity} x {item.service_name}" for item in items]
    return f"Réservation : {', '.join(lines)} — Total {total_price:.0f} {currency}"


def _validate_scheduled_at(db: Session, professional_id: uuid.UUID, scheduled_at: datetime) -> datetime:
    # Côte d'Ivoire runs on UTC+0 year-round (no DST), so a naive timestamp is
    # treated as already being in the professional's local time.
    if scheduled_at.tzinfo is None:
        scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)

    if scheduled_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="scheduled_at must be in the future")

    slots = db.query(Availability).filter(Availability.professional_id == professional_id).all()
    if slots:
        weekday = scheduled_at.weekday()
        local_time = scheduled_at.timetz().replace(tzinfo=None)
        matches = any(s.day_of_week == weekday and s.start_time <= local_time < s.end_time for s in slots)
        if not matches:
            raise HTTPException(
                status_code=400, detail="Ce créneau est en dehors des disponibilités du professionnel"
            )
    return scheduled_at


def _get_or_create_conversation(db: Session, client_id: uuid.UUID, professional_user_id: uuid.UUID) -> Conversation:
    conversation = (
        db.query(Conversation)
        .filter(Conversation.client_id == client_id, Conversation.professional_id == professional_user_id)
        .first()
    )
    if conversation:
        return conversation
    conversation = Conversation(client_id=client_id, professional_id=professional_user_id)
    db.add(conversation)
    db.flush()
    return conversation


@router.post("", response_model=BookingRead, status_code=201, summary="Create a booking request")
async def create_booking(
    payload: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.get(ProfessionalProfile, payload.professional_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Professional not found")
    if profile.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot book your own services")

    service_ids = [item.service_id for item in payload.items]
    services = (
        db.query(ProfessionalService)
        .filter(ProfessionalService.id.in_(service_ids), ProfessionalService.professional_id == payload.professional_id)
        .all()
    )
    services_by_id = {s.id: s for s in services}
    missing = set(service_ids) - services_by_id.keys()
    if missing:
        raise HTTPException(status_code=400, detail="One or more services do not belong to this professional")

    scheduled_at = _validate_scheduled_at(db, profile.id, payload.scheduled_at)
    conversation = _get_or_create_conversation(db, current_user.id, profile.user_id)

    booking_items: list[BookingItem] = []
    total_price = 0.0
    currency = "FCFA"
    for item in payload.items:
        service = services_by_id[item.service_id]
        subtotal = service.price * item.quantity
        total_price += subtotal
        currency = service.currency
        booking_items.append(
            BookingItem(
                service_id=service.id,
                service_name=service.name,
                unit=service.unit,
                unit_price=service.price,
                quantity=item.quantity,
                subtotal=subtotal,
            )
        )

    booking = Booking(
        conversation_id=conversation.id,
        client_id=current_user.id,
        professional_id=profile.id,
        address=payload.address,
        latitude=payload.latitude,
        longitude=payload.longitude,
        scheduled_at=scheduled_at,
        notes=payload.notes,
        total_price=total_price,
        currency=currency,
        items=booking_items,
    )
    db.add(booking)
    db.flush()

    message = Message(
        conversation_id=conversation.id,
        sender_id=current_user.id,
        content=_summary_text(booking_items, total_price, currency),
        message_type=MessageType.BOOKING,
        booking_id=booking.id,
    )
    db.add(message)
    db.commit()
    db.refresh(booking)
    db.refresh(message)

    payload_out = {"type": "message", "message": MessageRead.model_validate(message).model_dump(mode="json")}
    await manager.broadcast(conversation.id, payload_out)

    return booking


@router.get("/mine", response_model=list[BookingRead], summary="List the current user's bookings")
def list_my_bookings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    my_profile = db.query(ProfessionalProfile).filter(ProfessionalProfile.user_id == current_user.id).first()
    professional_id = my_profile.id if my_profile else None

    query = db.query(Booking).filter(
        or_(Booking.client_id == current_user.id, Booking.professional_id == professional_id)
    )
    return query.order_by(Booking.created_at.desc()).all()


@router.get("/{booking_id}", response_model=BookingRead, summary="Get a booking by id")
def get_booking(booking_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    profile = db.get(ProfessionalProfile, booking.professional_id)
    if current_user.id != booking.client_id and (not profile or profile.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not part of this booking")
    return booking


@router.patch(
    "/{booking_id}/status", response_model=BookingRead, summary="Accept, decline, complete or cancel a booking"
)
async def update_booking_status(
    booking_id: uuid.UUID,
    payload: BookingStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    profile = db.get(ProfessionalProfile, booking.professional_id)
    is_owner_professional = profile is not None and profile.user_id == current_user.id
    if not is_owner_professional and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only the professional can update this booking's status")

    allowed = _ALLOWED_TRANSITIONS.get(booking.status, set())
    if payload.status not in allowed:
        raise HTTPException(
            status_code=400, detail=f"Cannot move booking from {booking.status.value} to {payload.status.value}"
        )

    booking.status = payload.status
    db.commit()
    db.refresh(booking)

    payload_out = {"type": "booking_status", "booking": BookingRead.model_validate(booking).model_dump(mode="json")}
    await manager.broadcast(booking.conversation_id, payload_out)

    return booking
