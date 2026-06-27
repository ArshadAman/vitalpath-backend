from pydantic import BaseModel
from datetime import datetime

class NotificationCreate(BaseModel):
    notification_type: str
    title: str
    message: str

class NotificationResponse(NotificationCreate):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
