import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.message import Message, MessageType
from app.services.minio_client import remove_object

logger = logging.getLogger(__name__)

_EXPIRED_CAPTION = {
    MessageType.IMAGE: "📷 Photo (expirée)",
    MessageType.VIDEO: "🎥 Vidéo (expirée)",
    MessageType.AUDIO: "🎤 Note vocale (expirée)",
}

_MEDIA_TYPES = (MessageType.IMAGE, MessageType.VIDEO, MessageType.AUDIO)


def purge_expired_chat_media(db: Session) -> int:
    """Deletes chat media older than CHAT_MEDIA_RETENTION_DAYS from MinIO and
    clears the corresponding message fields. The message row itself is kept
    (with an "expired" caption) so the conversation history stays intact.

    Returns the number of messages purged.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.CHAT_MEDIA_RETENTION_DAYS)

    expired = db.execute(
        select(Message).where(
            Message.message_type.in_(_MEDIA_TYPES),
            Message.media_url.is_not(None),
            Message.created_at < cutoff,
        )
    ).scalars().all()

    for message in expired:
        if message.media_object_key:
            remove_object(message.media_object_key)
        message.content = _EXPIRED_CAPTION.get(message.message_type, "Média expiré")
        message.media_url = None
        message.media_mime_type = None
        message.media_duration_seconds = None
        message.media_object_key = None

    if expired:
        db.commit()
        logger.info("Purged %d expired chat media message(s)", len(expired))

    return len(expired)
