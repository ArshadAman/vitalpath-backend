from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from app.features.timeline.models import TimelineEvent
from app.features.timeline.schemas import TimelineEventCreate

def get_timeline_events(
    db: Session, 
    user_id: int, 
    event_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search_query: Optional[str] = None
) -> List[TimelineEvent]:
    """Retrieves and filters timeline events based on date ranges, types, and text queries."""
    query = db.query(TimelineEvent).filter(TimelineEvent.user_id == user_id)
    
    if event_type:
        query = query.filter(TimelineEvent.event_type == event_type)
        
    if start_date:
        query = query.filter(TimelineEvent.event_date >= start_date)
        
    if end_date:
        query = query.filter(TimelineEvent.event_date <= end_date)
        
    if search_query:
        search_filter = f"%{search_query}%"
        query = query.filter(
            (TimelineEvent.title.ilike(search_filter)) | 
            (TimelineEvent.description.ilike(search_filter))
        )
        
    return query.order_by(TimelineEvent.event_date.desc()).all()

def create_timeline_event(db: Session, user_id: int, event_data: TimelineEventCreate) -> TimelineEvent:
    """Creates a new timeline event."""
    db_event = TimelineEvent(
        user_id=user_id,
        **event_data.model_dump()
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event
