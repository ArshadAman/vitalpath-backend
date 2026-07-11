from fastapi import APIRouter, Depends, Query, status, HTTPException, Response
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from app.core.database import get_db
from app.features.timeline.schemas import TimelineEventResponse, TimelineEventCreate
from app.features.timeline.services import get_timeline_events, create_timeline_event
from app.features.timeline.models import TimelineEvent
from app.features.auth.services import get_current_user
from app.features.auth.models import User

router = APIRouter(prefix="/timeline", tags=["Health Timeline"])

@router.get("", response_model=List[TimelineEventResponse])
def read_timeline(
    current_user: User = Depends(get_current_user),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    search: Optional[str] = Query(None, description="Search term in title/description"),
    db: Session = Depends(get_db)
):
    """Retrieves list of health events on user health timeline, supporting search and filters."""
    return get_timeline_events(
        db=db, 
        user_id=current_user.id, 
        event_type=event_type, 
        start_date=start_date, 
        end_date=end_date, 
        search_query=search
    )

@router.post("", response_model=TimelineEventResponse, status_code=status.HTTP_201_CREATED)
def add_event(event_data: TimelineEventCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Creates a new health event on user timeline."""
    return create_timeline_event(db, current_user.id, event_data)

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Deletes a health event from timeline."""
    event = db.query(TimelineEvent).filter(TimelineEvent.id == event_id, TimelineEvent.user_id == current_user.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Timeline event not found")
    db.delete(event)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
