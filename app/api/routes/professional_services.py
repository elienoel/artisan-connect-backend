import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.professional import ProfessionalProfile
from app.models.service import ProfessionalService
from app.models.user import User, UserRole
from app.schemas.service import ProfessionalServiceCreate, ProfessionalServiceRead, ProfessionalServiceUpdate

router = APIRouter(prefix="/professionals/{professional_id}/services", tags=["professional-services"])


def _get_owned_profile(db: Session, professional_id: uuid.UUID, current_user: User) -> ProfessionalProfile:
    profile = db.get(ProfessionalProfile, professional_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Professional not found")
    if profile.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not allowed to manage this professional's services")
    return profile


@router.get("", response_model=list[ProfessionalServiceRead])
def list_services(professional_id: uuid.UUID, db: Session = Depends(get_db)):
    profile = db.get(ProfessionalProfile, professional_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Professional not found")
    return (
        db.query(ProfessionalService)
        .filter(ProfessionalService.professional_id == professional_id, ProfessionalService.is_active.is_(True))
        .order_by(ProfessionalService.position)
        .all()
    )


@router.post("", response_model=ProfessionalServiceRead, status_code=201)
def create_service(
    professional_id: uuid.UUID,
    payload: ProfessionalServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_owned_profile(db, professional_id, current_user)
    service = ProfessionalService(professional_id=professional_id, **payload.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.patch("/{service_id}", response_model=ProfessionalServiceRead)
def update_service(
    professional_id: uuid.UUID,
    service_id: uuid.UUID,
    payload: ProfessionalServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_owned_profile(db, professional_id, current_user)
    service = db.get(ProfessionalService, service_id)
    if not service or service.professional_id != professional_id:
        raise HTTPException(status_code=404, detail="Service not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(service, field, value)
    db.commit()
    db.refresh(service)
    return service


@router.delete("/{service_id}", status_code=204)
def delete_service(
    professional_id: uuid.UUID,
    service_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_owned_profile(db, professional_id, current_user)
    service = db.get(ProfessionalService, service_id)
    if not service or service.professional_id != professional_id:
        raise HTTPException(status_code=404, detail="Service not found")

    db.delete(service)
    db.commit()
