import uuid
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    """Tracks active websocket connections per conversation room."""

    def __init__(self) -> None:
        self._rooms: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)

    async def connect(self, conversation_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._rooms[conversation_id].add(websocket)

    def disconnect(self, conversation_id: uuid.UUID, websocket: WebSocket) -> None:
        self._rooms[conversation_id].discard(websocket)
        if not self._rooms[conversation_id]:
            self._rooms.pop(conversation_id, None)

    async def broadcast(self, conversation_id: uuid.UUID, payload: dict) -> None:
        dead = []
        for ws in self._rooms.get(conversation_id, set()):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(conversation_id, ws)


manager = ConnectionManager()
