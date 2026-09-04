from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.payment import Payment, PaymentPurpose, PaymentStatus
from app.models.professional import ProfessionalProfile, SubscriptionPlan
from app.models.user import User
from app.schemas.billing import BillingStatusRead, BoostRequest, PaymentRead, SubscribeRequest
from app.services.payment_gateway import charge

router = APIRouter(prefix="/billing", tags=["billing"])

# Simulated pricing — adjust once a real payment provider sets the actual rates.
PREMIUM_PRICE_FCFA = 5000
PREMIUM_DURATION_DAYS = 30
BOOST_DAILY_PRICE_FCFA = 500


def _own_profile(db: Session, current_user: User) -> ProfessionalProfile:
    profile = db.query(ProfessionalProfile).filter(ProfessionalProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No professional profile for this user")
    return profile


def _record_payment(
    db: Session, profile: ProfessionalProfile, purpose: PaymentPurpose, amount: float, reference: str, succeeded: bool
) -> Payment:
    payment = Payment(
        professional_id=profile.id,
        purpose=purpose,
        status=PaymentStatus.SUCCEEDED if succeeded else PaymentStatus.FAILED,
        amount=amount,
        currency="FCFA",
        provider="simulated",
        provider_reference=reference,
        paid_at=datetime.now(timezone.utc) if succeeded else None,
    )
    db.add(payment)
    return payment


@router.get(
    "/mine", response_model=BillingStatusRead, summary="Get the current professional's subscription and boost status"
)
def get_my_billing_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _own_profile(db, current_user)


@router.get("/payments", response_model=list[PaymentRead], summary="List the current professional's payment history")
def list_my_payments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = _own_profile(db, current_user)
    return (
        db.query(Payment)
        .filter(Payment.professional_id == profile.id)
        .order_by(Payment.created_at.desc())
        .all()
    )


@router.post(
    "/subscribe",
    response_model=BillingStatusRead,
    status_code=201,
    summary="Subscribe to the premium plan for 30 days (simulated payment)",
)
def subscribe(
    payload: SubscribeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    profile = _own_profile(db, current_user)
    result = charge(PREMIUM_PRICE_FCFA, "FCFA", "Abonnement premium (30 jours)")
    _record_payment(db, profile, PaymentPurpose.SUBSCRIPTION, PREMIUM_PRICE_FCFA, result.reference, result.success)

    if not result.success:
        db.commit()
        raise HTTPException(status_code=402, detail="Payment failed")

    now = datetime.now(timezone.utc)
    base = profile.subscription_expires_at if profile.subscription_expires_at and profile.subscription_expires_at > now else now
    profile.subscription_plan = SubscriptionPlan.PREMIUM
    profile.subscription_expires_at = base + timedelta(days=PREMIUM_DURATION_DAYS)
    db.commit()
    db.refresh(profile)
    return profile


@router.post(
    "/boost",
    response_model=BillingStatusRead,
    status_code=201,
    summary="Boost the profile's search ranking for N days (simulated payment)",
)
def boost(payload: BoostRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = _own_profile(db, current_user)
    amount = BOOST_DAILY_PRICE_FCFA * payload.days
    result = charge(amount, "FCFA", f"Mise en avant ({payload.days} jours)")
    _record_payment(db, profile, PaymentPurpose.BOOST, amount, result.reference, result.success)

    if not result.success:
        db.commit()
        raise HTTPException(status_code=402, detail="Payment failed")

    now = datetime.now(timezone.utc)
    base = profile.boosted_until if profile.boosted_until and profile.boosted_until > now else now
    profile.is_boosted = True
    profile.boosted_until = base + timedelta(days=payload.days)
    db.commit()
    db.refresh(profile)
    return profile
