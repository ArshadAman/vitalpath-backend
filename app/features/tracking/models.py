from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from datetime import datetime
from app.core.database import Base

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    steps = Column(Integer, default=0)
    distance_km = Column(Float, default=0.0)
    active_minutes = Column(Integer, default=0)
    date = Column(DateTime, default=datetime.utcnow, index=True)

class SleepLog(Base):
    __tablename__ = "sleep_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    duration_hours = Column(Float)
    quality_score = Column(Integer) # 1-10 or 1-100 scale
    date = Column(DateTime, default=datetime.utcnow, index=True)

class WeightLog(Base):
    __tablename__ = "weight_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    weight_kg = Column(Float)
    date = Column(DateTime, default=datetime.utcnow, index=True)

class BPLog(Base):
    __tablename__ = "bp_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    systolic = Column(Integer)
    diastolic = Column(Integer)
    date = Column(DateTime, default=datetime.utcnow, index=True)
