from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    auth,
    bookings,
    chat_ws,
    conversations,
    media,
    professional_services,
    professionals,
    professions,
    reviews,
)
from app.core.config import settings
from app.services.minio_client import ensure_bucket

TAGS_METADATA = [
    {"name": "auth", "description": "Registration, login and the current user's profile."},
    {"name": "professions", "description": "Catalogue of trades (plombier, electricien, ...)."},
    {"name": "professionals", "description": "Professional profiles: search, view, create and update."},
    {"name": "professional-services", "description": "Services (with pricing) offered by a professional."},
    {"name": "media", "description": "Avatar and portfolio photo/document uploads."},
    {"name": "conversations", "description": "Client/professional conversations and their messages."},
    {"name": "chat-ws", "description": "Realtime chat over WebSocket."},
    {"name": "bookings", "description": "Booking requests and their lifecycle (accept, decline, complete)."},
    {"name": "reviews", "description": "Client reviews left on completed bookings."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_bucket()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API REST pour Artisan Connect: mise en relation entre clients et artisans/professionnels.",
    version="1.0.0",
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(professions.router, prefix=settings.API_V1_PREFIX)
app.include_router(professionals.router, prefix=settings.API_V1_PREFIX)
app.include_router(professional_services.router, prefix=settings.API_V1_PREFIX)
app.include_router(media.router, prefix=settings.API_V1_PREFIX)
app.include_router(conversations.router, prefix=settings.API_V1_PREFIX)
app.include_router(bookings.router, prefix=settings.API_V1_PREFIX)
app.include_router(reviews.router, prefix=settings.API_V1_PREFIX)
app.include_router(chat_ws.router)


@app.get("/health")
def health():
    return {"status": "ok"}
