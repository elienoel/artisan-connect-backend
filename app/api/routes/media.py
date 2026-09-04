import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.conversation import Conversation
from app.models.media import Media, MediaType
from app.models.message import Message, MessageType
from app.models.professional import ProfessionalProfile
from app.models.user import User
from app.schemas.chat import MessageRead
from app.schemas.media import MediaRead
from app.schemas.user import UserRead
from app.services.minio_client import upload_file
from app.ws.manager import manager

router = APIRouter(prefix="/media", tags=["media"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_CHAT_TYPES = {
    "image/jpeg": (MessageType.IMAGE, "📷 Photo"),
    "image/png": (MessageType.IMAGE, "📷 Photo"),
    "image/webp": (MessageType.IMAGE, "📷 Photo"),
    "video/mp4": (MessageType.VIDEO, "🎥 Vidéo"),
    "video/quicktime": (MessageType.VIDEO, "🎥 Vidéo"),
    "audio/mp4": (MessageType.AUDIO, "🎤 Note vocale"),
    "audio/m4a": (MessageType.AUDIO, "🎤 Note vocale"),
    "audio/x-m4a": (MessageType.AUDIO, "🎤 Note vocale"),
    "audio/aac": (MessageType.AUDIO, "🎤 Note vocale"),
    "audio/mpeg": (MessageType.AUDIO, "🎤 Note vocale"),
    "audio/wav": (MessageType.AUDIO, "🎤 Note vocale"),
}
MAX_CHAT_IMAGE_SIZE = 15 * 1024 * 1024
MAX_CHAT_VIDEO_SIZE = 50 * 1024 * 1024
MAX_CHAT_AUDIO_SIZE = 15 * 1024 * 1024


@router.post("/users/me/avatar", response_model=UserRead, status_code=201, summary="Upload the current user's avatar")
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


@router.post(
    "/professionals/{professional_id}",
    response_model=MediaRead,
    status_code=201,
    summary="Upload a portfolio photo or document",
)
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


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageRead,
    status_code=201,
    summary="Send an image, video or voice note in a conversation",
)
async def upload_chat_media(
    conversation_id: uuid.UUID,
    file: UploadFile = File(...),
    duration_seconds: int | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if current_user.id not in (conversation.client_id, conversation.professional_id):
        raise HTTPException(status_code=403, detail="Not part of this conversation")

    match = ALLOWED_CHAT_TYPES.get(file.content_type)
    if not match:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    message_type, caption = match

    data = await file.read()
    max_size = {
        MessageType.IMAGE: MAX_CHAT_IMAGE_SIZE,
        MessageType.VIDEO: MAX_CHAT_VIDEO_SIZE,
        MessageType.AUDIO: MAX_CHAT_AUDIO_SIZE,
    }[message_type]
    if len(data) > max_size:
        raise HTTPException(status_code=400, detail=f"File too large (max {max_size // (1024 * 1024)}MB)")

    object_key, url = upload_file(data, file.content_type, folder=f"conversations/{conversation_id}")

    message = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=caption,
        message_type=message_type,
        media_url=url,
        media_mime_type=file.content_type,
        media_duration_seconds=duration_seconds,
        media_object_key=object_key,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    payload = {"type": "message", "message": MessageRead.model_validate(message).model_dump(mode="json")}
    await manager.broadcast(conversation_id, payload)

    return message
