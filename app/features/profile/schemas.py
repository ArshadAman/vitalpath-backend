from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class HealthProfileBase(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    blood_group: Optional[str] = None
    
    has_diabetes: Optional[str] = "no"
    has_hypertension: Optional[str] = "no"
    has_cholesterol: Optional[str] = "no"
    has_liver_disease: Optional[str] = "no"
    has_heart_disease: Optional[str] = "no"
    
    family_diabetes: Optional[str] = "no"
    family_heart_disease: Optional[str] = "no"
    family_hypertension: Optional[str] = "no"
    family_cancer: Optional[str] = "no"
    
    smoking_status: Optional[str] = "never"
    alcohol_consumption: Optional[str] = "none"
    diet_type: Optional[str] = "mixed"
    exercise_frequency: Optional[str] = "rarely"

class HealthProfileCreate(HealthProfileBase):
    pass

class HealthProfileUpdate(HealthProfileBase):
    pass

class HealthProfileResponse(HealthProfileBase):
    id: int
    user_id: int
    updated_at: datetime

    class Config:
        from_attributes = True
