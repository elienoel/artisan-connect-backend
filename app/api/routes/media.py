import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.media import Media, MediaType
from app.models.professional import ProfessionalProfile
from app.models.user import User
from app.schemas.media import MediaRead
from app.schemas.user import UserRead
from app.services.minio_client import upload_file

router = APIRouter(prefix="/media", tags=["media"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/users/me/avatar", response_model=UserRead, status_code=201)
async def upload_my_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    _, url = upload_file(data, file.content_type, folder=f"users/{current_user.id}/avatar")
    current_user.avatar_url = url
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/professionals/{professional_id}", response_model=MediaRead, status_code=201)
async def upload_professional_media(
    professional_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.get(ProfessionalProfile, professional_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Professional not found")
    if profile.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to upload media for this profile")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    media_type = MediaType.PHOTO if file.content_type.startswith("image/") else MediaType.DOCUMENT
    object_key, url = upload_file(data, file.content_type, folder=f"professionals/{professional_id}")

    media = Media(professional_id=professional_id, object_key=object_key, url=url, media_type=media_type)
    db.add(media)
    db.commit()
    db.refresh(media)
    return media
