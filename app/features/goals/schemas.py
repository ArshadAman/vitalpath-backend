from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class GoalBase(BaseModel):
    goal_type: str
    title: str
    target_value: float
    current_value: Optional[float] = 0.0
    unit: str
    target_date: datetime

class GoalCreate(GoalBase):
    pass

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    status: Optional[str] = None
    target_date: Optional[datetime] = None

class GoalResponse(GoalBase):
    id: int
    user_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
