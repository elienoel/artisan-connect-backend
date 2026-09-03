from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.profession import Profession
from app.models.user import User, UserRole
from app.schemas.profession import ProfessionCreate, ProfessionRead

router = APIRouter(prefix="/professions", tags=["professions"])


@router.get("", response_model=list[ProfessionRead], summary="List active professions")
def list_professions(db: Session = Depends(get_db)):
    return db.query(Profession).filter(Profession.is_active.is_(True)).order_by(Profession.name).all()


@router.post("", response_model=ProfessionRead, status_code=201, summary="Create a profession (admin only)")
def create_profession(
    payload: ProfessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    if db.query(Profession).filter(Profession.slug == payload.slug).first():
        raise HTTPException(status_code=400, detail="Profession slug already exists")
    profession = Profession(**payload.model_dump())
    db.add(profession)
    db.commit()
    db.refresh(profession)
    return profession
