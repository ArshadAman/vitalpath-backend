from pydantic import BaseModel, Field
from datetime import datetime

class ActivityCreate(BaseModel):
    steps: int = Field(..., ge=0)
    distance_km: float = Field(..., ge=0.0)
    active_minutes: int = Field(..., ge=0)
    date: datetime

class ActivityResponse(ActivityCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class SleepCreate(BaseModel):
    duration_hours: float = Field(..., ge=0.0)
    quality_score: int = Field(..., ge=1, le=100)
    date: datetime

class SleepResponse(SleepCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class WeightCreate(BaseModel):
    weight_kg: float = Field(..., ge=0.0)
    date: datetime

class WeightResponse(WeightCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class BPCreate(BaseModel):
    systolic: int = Field(..., ge=40, le=250)
    diastolic: int = Field(..., ge=40, le=150)
    date: datetime

class BPResponse(BPCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True
