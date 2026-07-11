from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.features.profile.schemas import HealthProfileResponse, HealthProfileCreate, HealthProfileUpdate
from app.features.profile.services import (
    get_health_profile, create_health_profile, update_health_profile
)
from app.features.auth.services import get_current_user
from app.features.auth.models import User
from app.features.score.services import calculate_health_metrics

router = APIRouter(prefix="/profile", tags=["Health Profiles"])

@router.get("", response_model=HealthProfileResponse)
def read_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieves the health profile details for the authenticated user."""
    profile = get_health_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Health profile not found")
    return profile

@router.post("", response_model=HealthProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(profile_data: HealthProfileCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Creates a new health profile for the authenticated user."""
    existing_profile = get_health_profile(db, current_user.id)
    if existing_profile:
        raise HTTPException(status_code=400, detail="Profile already exists for this user")
    profile = create_health_profile(db, current_user.id, profile_data)
    calculate_health_metrics(db, current_user.id)
    return profile

@router.put("", response_model=HealthProfileResponse)
def update_profile(profile_data: HealthProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Updates the health profile details for the authenticated user."""
    profile = get_health_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Health profile not found")
    updated = update_health_profile(db, profile, profile_data)
    calculate_health_metrics(db, current_user.id)
    return updated
