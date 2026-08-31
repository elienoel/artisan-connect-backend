import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.chat import ConversationCreate, ConversationRead, MessageRead

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationRead])
def list_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conversations = (
        db.query(Conversation)
        .filter(or_(Conversation.client_id == current_user.id, Conversation.professional_id == current_user.id))
        .order_by(Conversation.created_at.desc())
        .all()
    )

    result = []
    for conv in conversations:
        other_id = conv.professional_id if conv.client_id == current_user.id else conv.client_id
        other_user = db.get(User, other_id)
        last_message = (
            db.query(Message)
            .filter(Message.conversation_id == conv.id)
            .order_by(Message.created_at.desc())
            .first()
        )
        result.append(
            ConversationRead(
                id=conv.id,
                client_id=conv.client_id,
                professional_id=conv.professional_id,
                created_at=conv.created_at,
                other_user=other_user,
                last_message=last_message,
            )
        )
    return result


@router.post("", response_model=ConversationRead, status_code=201)
def start_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.professional_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot start a conversation with yourself")

    existing = (
        db.query(Conversation)
        .filter(
            Conversation.client_id == current_user.id,
            Conversation.professional_id == payload.professional_user_id,
        )
        .first()
    )
    if existing:
        return ConversationRead(
            id=existing.id,
            client_id=existing.client_id,
            professional_id=existing.professional_id,
            created_at=existing.created_at,
            other_user=db.get(User, existing.professional_id),
        )

    conversation = Conversation(client_id=current_user.id, professional_id=payload.professional_user_id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return ConversationRead(
        id=conversation.id,
        client_id=conversation.client_id,
        professional_id=conversation.professional_id,
        created_at=conversation.created_at,
        other_user=db.get(User, conversation.professional_id),
    )


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
def get_messages(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if current_user.id not in (conversation.client_id, conversation.professional_id):
        raise HTTPException(status_code=403, detail="Not part of this conversation")

    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .all()
    )
