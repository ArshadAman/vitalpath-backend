from sqlalchemy.orm import Session
from typing import List, Optional
from app.features.notifications.models import Notification
from app.features.notifications.schemas import NotificationCreate
from app.features.notifications.tasks import send_push_notification_task

def get_user_notifications(db: Session, user_id: int) -> List[Notification]:
    """Retrieves all notifications for a user."""
    return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()

def mark_as_read(db: Session, notification_id: int) -> Optional[Notification]:
    """Marks a single log entry as read."""
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if notif:
        notif.is_read = True
        db.commit()
        db.refresh(notif)
    return notif

def create_notification(db: Session, user_id: int, notif_data: NotificationCreate) -> Notification:
    """Inserts notification log in Postgres and triggers an asynchronous Celery task for push dispatch."""
    notif = Notification(
        user_id=user_id,
        **notif_data.model_dump()
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    
    # Schedule celery push dispatch
    send_push_notification_task.delay(user_id, notif.title, notif.message)
    return notif
