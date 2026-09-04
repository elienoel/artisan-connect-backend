import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_current_user_optional
from app.core.database import get_db
from app.models.favorite import Favorite
from app.models.professional import ProfessionalProfile
from app.models.user import User, UserRole
from app.schemas.professional import (
    ProfessionalProfileCreate,
    ProfessionalProfileRead,
    ProfessionalProfileUpdate,
)
from app.schemas.service import ProfessionalServiceRead
from app.services.geo import haversine_km_expr

router = APIRouter(prefix="/professionals", tags=["professionals"])

_RELATIONS = (
    joinedload(ProfessionalProfile.profession),
    joinedload(ProfessionalProfile.user),
    joinedload(ProfessionalProfile.media),
    joinedload(ProfessionalProfile.services),
)


def _to_read_model(
    profile: ProfessionalProfile,
    distance_km: float | None = None,
    include_inactive_services: bool = False,
    is_favorite: bool = False,
) -> ProfessionalProfileRead:
    data = ProfessionalProfileRead.model_validate(profile)
    data.distance_km = round(distance_km, 2) if distance_km is not None else None
    data.photo_urls = [m.url for m in profile.media]
    services = profile.services if include_inactive_services else [s for s in profile.services if s.is_active]
    data.services = [ProfessionalServiceRead.model_validate(s) for s in services]
    data.is_favorite = is_favorite
    return data


def _favorite_ids(db: Session, current_user: User | None, professional_ids: list[uuid.UUID]) -> set[uuid.UUID]:
    if not current_user or not professional_ids:
        return set()
    rows = db.execute(
        select(Favorite.professional_id).where(
            Favorite.client_id == current_user.id, Favorite.professional_id.in_(professional_ids)
        )
    ).scalars().all()
    return set(rows)


@router.get("/search", response_model=list[ProfessionalProfileRead], summary="Search professionals near a location")
def search_professionals(
    lat: float = Query(..., description="Latitude of the search center"),
    lng: float = Query(..., description="Longitude of the search center"),
    radius_km: float = Query(15, ge=0.1, le=200),
    profession_id: uuid.UUID | None = None,
    q: str | None = Query(None, description="Free text search on business name"),
    min_rating: float | None = Query(None, ge=0, le=5, description="Only professionals rated at least this high"),
    max_price: float | None = Query(None, ge=0, description="Only professionals with an hourly rate at or below this"),
    sort: Literal["distance", "rating", "price"] = Query("distance", description="How to order the results"),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    distance = haversine_km_expr(ProfessionalProfile.latitude, ProfessionalProfile.longitude, lat, lng)

    # Intentionally not filtering on `is_verified` / `verification_status`
    # yet: professionals show up here whether or not their identity has
    # been validated by an admin. Once the app is ready to gate visibility
    # on that (e.g. once clients can tell verified profiles apart in the
    # UI), add `.where(ProfessionalProfile.is_verified.is_(True))` here.
    stmt = (
        select(ProfessionalProfile, distance.label("distance_km"))
        .options(*_RELATIONS)
        .where(distance <= radius_km)
    )
    if profession_id:
        stmt = stmt.where(ProfessionalProfile.profession_id == profession_id)
    if q:
        stmt = stmt.where(ProfessionalProfile.business_name.ilike(f"%{q}%"))
    if min_rating is not None:
        stmt = stmt.where(ProfessionalProfile.rating_avg >= min_rating)
    if max_price is not None:
        stmt = stmt.where(
            ProfessionalProfile.hourly_rate.is_not(None), ProfessionalProfile.hourly_rate <= max_price
        )
    if current_user:
        stmt = stmt.where(ProfessionalProfile.user_id != current_user.id)

    # Boosted profiles (paid "mise en avant") always come first, regardless
    # of the chosen sort — it only breaks ties among boosted/non-boosted.
    boost_priority = case(
        (and_(ProfessionalProfile.is_boosted.is_(True), ProfessionalProfile.boosted_until > func.now()), 0),
        else_=1,
    )
    secondary_order = {
        "distance": distance,
        "rating": ProfessionalProfile.rating_avg.desc(),
        "price": ProfessionalProfile.hourly_rate.asc().nulls_last(),
    }[sort]
    stmt = stmt.order_by(boost_priority, secondary_order)

    rows = db.execute(stmt).unique().all()
    favorite_ids = _favorite_ids(db, current_user, [profile.id for profile, _ in rows])
    return [_to_read_model(profile, dist, is_favorite=profile.id in favorite_ids) for profile, dist in rows]


@router.get("/me", response_model=ProfessionalProfileRead, summary="Get the current user's professional profile")
def get_my_professional_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = (
        db.query(ProfessionalProfile)
        .options(*_RELATIONS)
        .filter(ProfessionalProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="No professional profile for this user")
    return _to_read_model(profile, include_inactive_services=True)


@router.get(
    "/by-user/{user_id}", response_model=ProfessionalProfileRead, summary="Get a professional profile by user id"
)
def get_professional_by_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    profile = (
        db.query(ProfessionalProfile)
        .options(*_RELATIONS)
        .filter(ProfessionalProfile.user_id == user_id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Professional not found")
    is_favorite = bool(_favorite_ids(db, current_user, [profile.id]))
    return _to_read_model(profile, is_favorite=is_favorite)


@router.get("/{professional_id}", response_model=ProfessionalProfileRead, summary="Get a professional profile by id")
def get_professional(
    professional_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    profile = (
        db.query(ProfessionalProfile)
        .options(*_RELATIONS)
        .filter(ProfessionalProfile.id == professional_id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Professional not found")
    is_favorite = bool(_favorite_ids(db, current_user, [profile.id]))
    return _to_read_model(profile, is_favorite=is_favorite)


@router.post(
    "", response_model=ProfessionalProfileRead, status_code=201, summary="Create the current user's professional profile"
)
def create_professional_profile(
    payload: ProfessionalProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if db.query(ProfessionalProfile).filter(ProfessionalProfile.user_id == current_user.id).first():
        raise HTTPException(status_code=400, detail="Professional profile already exists for this user")

    current_user.role = UserRole.PROFESSIONAL
    profile = ProfessionalProfile(user_id=current_user.id, **payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return _to_read_model(profile, include_inactive_services=True)


@router.patch("/{professional_id}", response_model=ProfessionalProfileRead, summary="Update a professional profile")
def update_professional_profile(
    professional_id: uuid.UUID,
    payload: ProfessionalProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.get(ProfessionalProfile, professional_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Professional not found")
    if profile.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not allowed to edit this profile")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return _to_read_model(profile, include_inactive_services=True)
