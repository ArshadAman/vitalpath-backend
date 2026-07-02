from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class HealthProfileBase(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    bloodGroup: Optional[str] = None
    
    # Custom Targets
    waterTarget: Optional[int] = 2000
    sleepTarget: Optional[float] = 8.0
    calorieTarget: Optional[int] = 2000
    
    # Clinical profiles
    allergies: Optional[str] = None
    medications: Optional[str] = None
    
    # SaaS Health Parameters
    healthGoal: Optional[str] = "wellness"
    emergencyContactName: Optional[str] = None
    emergencyContactPhone: Optional[str] = None
    
    # Flags mapping
    diabetes: Optional[bool] = False
    hypertension: Optional[bool] = False
    heartDisease: Optional[bool] = False
    strokeHistory: Optional[bool] = False
    
    # Lifestyle choices mapping
    smoking: Optional[str] = "none"
    activity: Optional[str] = "active"
    diet: Optional[str] = "balanced"

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
