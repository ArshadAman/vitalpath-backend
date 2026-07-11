from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from datetime import datetime
from app.core.database import Base

class MedicalReport(Base):
    __tablename__ = "medical_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    file_name = Column(String)
    file_path = Column(String) # Local path or S3 key
    status = Column(String, default="pending") # pending, processing, completed, failed
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Storing whitelisted clinical parameters in JSONB
    metrics = Column(JSON, default=list)
