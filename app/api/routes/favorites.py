import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.professionals import _RELATIONS, _to_read_model
from app.core.database import get_db
from app.models.favorite import Favorite
from app.models.professional import ProfessionalProfile
from app.models.user import User
from app.schemas.favorite import FavoriteStatus
from app.schemas.professional import ProfessionalProfileRead

router = APIRouter(tags=["favorites"])


@router.get("/favorites/mine", response_model=list[ProfessionalProfileRead], summary="List the current user's favorite professionals")
def list_my_favorites(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = (
        select(ProfessionalProfile)
        .options(*_RELATIONS)
        .join(Favorite, Favorite.professional_id == ProfessionalProfile.id)
        .where(Favorite.client_id == current_user.id)
        .order_by(Favorite.created_at.desc())
    )
    profiles = db.execute(stmt).unique().scalars().all()
    return [_to_read_model(profile, is_favorite=True) for profile in profiles]


@router.post(
    "/professionals/{professional_id}/favorite",
    response_model=FavoriteStatus,
    status_code=201,
    summary="Add a professional to the current user's favorites",
)
def add_favorite(
    professional_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if not db.get(ProfessionalProfile, professional_id):
        raise HTTPException(status_code=404, detail="Professional not found")

    existing = (
        db.query(Favorite)
        .filter(Favorite.client_id == current_user.id, Favorite.professional_id == professional_id)
        .first()
    )
    if not existing:
        db.add(Favorite(client_id=current_user.id, professional_id=professional_id))
        db.commit()
    return FavoriteStatus(is_favorite=True)


@router.delete(
    "/professionals/{professional_id}/favorite",
    response_model=FavoriteStatus,
    summary="Remove a professional from the current user's favorites",
)
def remove_favorite(
    professional_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    db.query(Favorite).filter(
        Favorite.client_id == current_user.id, Favorite.professional_id == professional_id
    ).delete()
    db.commit()
    return FavoriteStatus(is_favorite=False)
