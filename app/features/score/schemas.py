from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

class HealthScoreResponse(BaseModel):
    id: int
    user_id: int
    score: int
    health_age: int
    factors: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
