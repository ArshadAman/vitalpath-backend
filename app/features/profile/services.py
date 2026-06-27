from typing import Optional
from sqlalchemy.orm import Session
from app.features.profile.models import HealthProfile
from app.features.profile.schemas import HealthProfileCreate, HealthProfileUpdate

def get_health_profile(db: Session, user_id: int) -> Optional[HealthProfile]:
    """Retrieves health profile by user ID."""
    return db.query(HealthProfile).filter(HealthProfile.user_id == user_id).first()

def create_health_profile(db: Session, user_id: int, profile_data: HealthProfileCreate) -> HealthProfile:
    """Creates a new health profile entry for a user."""
    db_profile = HealthProfile(
        user_id=user_id,
        **profile_data.model_dump()
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

def update_health_profile(db: Session, db_profile: HealthProfile, update_data: HealthProfileUpdate) -> HealthProfile:
    """Updates an existing health profile entry."""
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(db_profile, key, value)
    db.commit()
    db.refresh(db_profile)
    return db_profile
