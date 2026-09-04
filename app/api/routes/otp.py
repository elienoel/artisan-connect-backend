import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.otp import OtpChannel, OtpCode
from app.models.user import User
from app.schemas.otp import OtpRequest, OtpVerify
from app.schemas.user import UserRead
from app.services.otp_sender import send_otp

router = APIRouter(prefix="/auth/otp", tags=["auth"])

CODE_TTL_MINUTES = 10


def _destination(user: User, channel: OtpChannel) -> str:
    destination = user.phone if channel == OtpChannel.PHONE else user.email
    if not destination:
        raise HTTPException(status_code=400, detail=f"No {channel.value} on file for this account")
    return destination


@router.post("/request", status_code=204, summary="Request a one-time code to verify a phone number or email")
def request_otp(
    payload: OtpRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    destination = _destination(current_user, payload.channel)

    code = f"{secrets.randbelow(1_000_000):06d}"
    db.add(
        OtpCode(
            user_id=current_user.id,
            channel=payload.channel,
            code=code,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=CODE_TTL_MINUTES),
        )
    )
    db.commit()

    send_otp(payload.channel, destination, code)


@router.post("/verify", response_model=UserRead, summary="Confirm a phone number or email with its one-time code")
def verify_otp(
    payload: OtpVerify, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    otp = (
        db.query(OtpCode)
        .filter(
            OtpCode.user_id == current_user.id,
            OtpCode.channel == payload.channel,
            OtpCode.consumed_at.is_(None),
            OtpCode.expires_at > datetime.now(timezone.utc),
        )
        .order_by(OtpCode.created_at.desc())
        .first()
    )
    if not otp or not secrets.compare_digest(otp.code, payload.code):
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    otp.consumed_at = datetime.now(timezone.utc)
    if payload.channel == OtpChannel.PHONE:
        current_user.phone_verified_at = datetime.now(timezone.utc)
    else:
        current_user.email_verified_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(current_user)
    return current_user
