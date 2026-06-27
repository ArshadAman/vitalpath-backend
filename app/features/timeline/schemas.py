from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class TimelineEventBase(BaseModel):
    event_type: str
    event_date: datetime
    title: str
    description: Optional[str] = None
    payload: Dict[str, Any] = {}

class TimelineEventCreate(TimelineEventBase):
    pass

class TimelineEventResponse(TimelineEventBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
