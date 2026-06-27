from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from datetime import datetime
from app.core.database import Base

class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Goal types: lose_weight, quit_smoking, reduce_hba1c, improve_sleep
    goal_type = Column(String, index=True)
    title = Column(String)
    
    target_value = Column(Float)
    current_value = Column(Float, default=0.0)
    unit = Column(String)
    
    status = Column(String, default="active") # active, completed, failed
    target_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
