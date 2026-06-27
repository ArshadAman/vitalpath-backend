from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from datetime import datetime
from app.core.database import Base

class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Event types: blood_report, doctor_visit, hospital_visit, weight_update, exercise, medication_change, goal, location_context
    event_type = Column(String, index=True)
    event_date = Column(DateTime, default=datetime.utcnow, index=True)
    title = Column(String)
    description = Column(String, nullable=True)
    
    # Extra payload containing event parameters (e.g. weight value, medication name, steps, heart rate etc.)
    payload = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
