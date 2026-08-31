import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.api.deps import get_current_user_ws
from app.core.database import SessionLocal
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import MessageRead, WSMessageIn
from app.ws.manager import manager

router = APIRouter(tags=["chat-ws"])


@router.websocket("/ws/chat/{conversation_id}")
async def chat_websocket(websocket: WebSocket, conversation_id: uuid.UUID, token: str):
    db = SessionLocal()
    try:
        user = get_current_user_ws(token, db)
        if user is None:
            await websocket.close(code=4401)
            return

        conversation = db.get(Conversation, conversation_id)
        if conversation is None or user.id not in (conversation.client_id, conversation.professional_id):
            await websocket.close(code=4403)
            return

        await manager.connect(conversation_id, websocket)
        try:
            while True:
                raw = await websocket.receive_json()
                try:
                    incoming = WSMessageIn.model_validate(raw)
                except ValidationError:
                    continue

                message = Message(
                    conversation_id=conversation_id,
                    sender_id=user.id,
                    content=incoming.content,
                )
                db.add(message)
                db.commit()
                db.refresh(message)

                payload = {"type": "message", "message": MessageRead.model_validate(message).model_dump(mode="json")}
                await manager.broadcast(conversation_id, payload)
        except WebSocketDisconnect:
            manager.disconnect(conversation_id, websocket)
    finally:
        db.close()
