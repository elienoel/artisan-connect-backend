import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_admin, get_current_user
from app.core.database import get_db
from app.models.professional import ProfessionalProfile, VerificationStatus
from app.models.user import User
from app.schemas.verification import VerificationDetailRead, VerificationQueueItem, VerificationReject
from app.services.minio_client import upload_file

router = APIRouter(tags=["verification"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024


def _get_own_profile(db: Session, current_user: User) -> ProfessionalProfile:
    profile = db.query(ProfessionalProfile).filter(ProfessionalProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No professional profile for this user")
    return profile


@router.post(
    "/professionals/me/verification",
    response_model=VerificationDetailRead,
    status_code=201,
    summary="Submit (or resubmit) an identity document for verification",
)
async def submit_verification_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = _get_own_profile(db, current_user)
    if profile.verification_status == VerificationStatus.VERIFIED:
        raise HTTPException(status_code=400, detail="This profile is already verified")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    object_key, url = upload_file(data, file.content_type, folder=f"professionals/{profile.id}/verification")

    profile.verification_document_url = url
    profile.verification_document_object_key = object_key
    profile.verification_status = VerificationStatus.PENDING
    profile.verification_submitted_at = datetime.now(timezone.utc)
    profile.verification_reviewed_at = None
    profile.verification_rejection_reason = None
    db.commit()
    db.refresh(profile)
    return profile


@router.get(
    "/professionals/me/verification",
    response_model=VerificationDetailRead,
    summary="Get the current professional's verification status",
)
def get_my_verification(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get_own_profile(db, current_user)


@router.get(
    "/admin/verifications",
    response_model=list[VerificationQueueItem],
    summary="List professionals awaiting identity verification (admin only)",
)
def list_pending_verifications(db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    stmt = (
        select(ProfessionalProfile)
        .options(joinedload(ProfessionalProfile.user))
        .where(ProfessionalProfile.verification_status == VerificationStatus.PENDING)
        .order_by(ProfessionalProfile.verification_submitted_at)
    )
    return db.execute(stmt).unique().scalars().all()


@router.post(
    "/admin/verifications/{professional_id}/approve",
    response_model=VerificationDetailRead,
    summary="Approve a professional's identity verification (admin only)",
)
def approve_verification(
    professional_id: uuid.UUID, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)
):
    profile = db.get(ProfessionalProfile, professional_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Professional not found")
    profile.verification_status = VerificationStatus.VERIFIED
    profile.is_verified = True
    profile.verification_reviewed_at = datetime.now(timezone.utc)
    profile.verification_rejection_reason = None
    db.commit()
    db.refresh(profile)
    return profile


@router.post(
    "/admin/verifications/{professional_id}/reject",
    response_model=VerificationDetailRead,
    summary="Reject a professional's identity verification (admin only)",
)
def reject_verification(
    professional_id: uuid.UUID,
    payload: VerificationReject,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    profile = db.get(ProfessionalProfile, professional_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Professional not found")
    profile.verification_status = VerificationStatus.REJECTED
    profile.is_verified = False
    profile.verification_reviewed_at = datetime.now(timezone.utc)
    profile.verification_rejection_reason = payload.reason
    db.commit()
    db.refresh(profile)
    return profile
