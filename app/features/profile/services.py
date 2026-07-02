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
        name=profile_data.name,
        age=profile_data.age,
        gender=profile_data.gender,
        height=profile_data.height,
        weight=profile_data.weight,
        blood_group=profile_data.bloodGroup,
        water_target=profile_data.waterTarget,
        sleep_target=profile_data.sleepTarget,
        calorie_target=profile_data.calorieTarget,
        allergies=profile_data.allergies,
        medications=profile_data.medications,
        health_goal=profile_data.healthGoal,
        emergency_contact_name=profile_data.emergencyContactName,
        emergency_contact_phone=profile_data.emergencyContactPhone,
        has_diabetes="yes" if profile_data.diabetes else "no",
        has_hypertension="yes" if profile_data.hypertension else "no",
        has_heart_disease="yes" if profile_data.heartDisease else "no",
        has_stroke="yes" if profile_data.strokeHistory else "no",
        smoking_status=profile_data.smoking,
        exercise_frequency=profile_data.activity,
        diet_type=profile_data.diet
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

def update_health_profile(db: Session, db_profile: HealthProfile, update_data: HealthProfileUpdate) -> HealthProfile:
    """Updates an existing health profile entry."""
    if update_data.name is not None: db_profile.name = update_data.name
    if update_data.age is not None: db_profile.age = update_data.age
    if update_data.gender is not None: db_profile.gender = update_data.gender
    if update_data.height is not None: db_profile.height = update_data.height
    if update_data.weight is not None: db_profile.weight = update_data.weight
    if update_data.bloodGroup is not None: db_profile.blood_group = update_data.bloodGroup
    if update_data.waterTarget is not None: db_profile.water_target = update_data.waterTarget
    if update_data.sleepTarget is not None: db_profile.sleep_target = update_data.sleepTarget
    if update_data.calorieTarget is not None: db_profile.calorie_target = update_data.calorieTarget
    if update_data.allergies is not None: db_profile.allergies = update_data.allergies
    if update_data.medications is not None: db_profile.medications = update_data.medications
    if update_data.healthGoal is not None: db_profile.health_goal = update_data.healthGoal
    if update_data.emergencyContactName is not None: db_profile.emergency_contact_name = update_data.emergencyContactName
    if update_data.emergencyContactPhone is not None: db_profile.emergency_contact_phone = update_data.emergencyContactPhone
    if update_data.diabetes is not None: db_profile.has_diabetes = "yes" if update_data.diabetes else "no"
    if update_data.hypertension is not None: db_profile.has_hypertension = "yes" if update_data.hypertension else "no"
    if update_data.heartDisease is not None: db_profile.has_heart_disease = "yes" if update_data.heartDisease else "no"
    if update_data.strokeHistory is not None: db_profile.has_stroke = "yes" if update_data.strokeHistory else "no"
    if update_data.smoking is not None: db_profile.smoking_status = update_data.smoking
    if update_data.activity is not None: db_profile.exercise_frequency = update_data.activity
    if update_data.diet is not None: db_profile.diet_type = update_data.diet
    
    db.commit()
    db.refresh(db_profile)
    return db_profile
