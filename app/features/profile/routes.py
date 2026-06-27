from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.features.profile.schemas import HealthProfileResponse, HealthProfileCreate, HealthProfileUpdate
from app.features.profile.services import get_health_profile, create_health_profile, update_health_profile

router = APIRouter(prefix="/profile", tags=["User Profile"])

@router.get("", response_model=HealthProfileResponse)
def read_profile(user_id: int, db: Session = Depends(get_db)):
    """Retrieves health profile details for a given user ID."""
    profile = get_health_profile(db, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Health profile not found")
    return profile

@router.post("", response_model=HealthProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(user_id: int, profile_data: HealthProfileCreate, db: Session = Depends(get_db)):
    """Creates a new health profile for a user ID."""
    existing_profile = get_health_profile(db, user_id)
    if existing_profile:
        raise HTTPException(status_code=400, detail="Profile already exists for this user")
    return create_health_profile(db, user_id, profile_data)

@router.put("", response_model=HealthProfileResponse)
def update_profile(user_id: int, profile_data: HealthProfileUpdate, db: Session = Depends(get_db)):
    """Updates the health profile details."""
    profile = get_health_profile(db, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Health profile not found")
    return update_health_profile(db, profile, profile_data)
