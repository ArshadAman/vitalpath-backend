from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.features.notifications.schemas import NotificationResponse
from app.features.notifications.services import get_user_notifications, mark_as_read

router = APIRouter(prefix="/notifications", tags=["Notifications Engine"])

@router.get("", response_model=List[NotificationResponse])
def read_notifications(user_id: int, db: Session = Depends(get_db)):
    """Retrieves notifications history for a user ID."""
    return get_user_notifications(db, user_id)

@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(notification_id: int, db: Session = Depends(get_db)):
    """Toggles read state of notification to True."""
    notif = mark_as_read(db, notification_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif
