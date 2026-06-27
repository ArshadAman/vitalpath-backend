from sqlalchemy import Column, Integer, ForeignKey, DateTime, JSON
from datetime import datetime
from app.core.database import Base

class HealthScoreLog(Base):
    __tablename__ = "health_score_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    score = Column(Integer)
    health_age = Column(Integer)
    
    # Breakdown breakdown of contribution parameters
    factors = Column(JSON, default=dict) 
    created_at = Column(DateTime, default=datetime.utcnow)
