import logging
from contextlib import asynccontextmanager
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    auth,
    availability,
    bookings,
    chat_ws,
    conversations,
    favorites,
    media,
    professional_services,
    professionals,
    professions,
    reviews,
    verification,
)

# billing (needs a payment provider) and otp (needs an SMS provider) are
# built and DB-backed (see app/models/payment.py, app/models/otp.py) but not
# wired into the app below, since neither has real credentials yet — see the
# app.api.routes.billing / app.api.routes.otp import lines and their
# app.include_router() calls further down for how to turn them back on.
# from app.api.routes import billing, otp
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.media_retention import purge_expired_chat_media
from app.services.minio_client import ensure_bucket

logger = logging.getLogger(__name__)


def _run_chat_media_purge() -> None:
    db = SessionLocal()
    try:
        purge_expired_chat_media(db)
    except Exception:
        logger.exception("Chat media purge job failed")
    finally:
        db.close()

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
    {"name": "verification", "description": "Professional identity verification: submission and admin review."},
    {"name": "favorites", "description": "A client's saved list of favorite professionals."},
    {"name": "availability", "description": "A professional's declared weekly working hours."},
    # "billing" and "otp" tags omitted while those routers are disabled — see the note above the imports.
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_bucket()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(_run_chat_media_purge, "interval", days=1, next_run_time=datetime.now())
    scheduler.start()

    yield

    scheduler.shutdown(wait=False)


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
app.include_router(verification.router, prefix=settings.API_V1_PREFIX)
app.include_router(favorites.router, prefix=settings.API_V1_PREFIX)
app.include_router(availability.router, prefix=settings.API_V1_PREFIX)
# app.include_router(otp.router, prefix=settings.API_V1_PREFIX)
# app.include_router(billing.router, prefix=settings.API_V1_PREFIX)
app.include_router(chat_ws.router)


@app.get("/health")
def health():
    return {"status": "ok"}
