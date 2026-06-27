from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
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

    metrics = relationship("ExtractedMetric", back_populates="report", cascade="all, delete-orphan")

class ExtractedMetric(Base):
    __tablename__ = "extracted_metrics"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("medical_reports.id"))
    
    test_name = Column(String, index=True) # e.g., HbA1c, LDL
    value = Column(Float)
    unit = Column(String)
    reference_range = Column(String, nullable=True)
    test_date = Column(DateTime, default=datetime.utcnow)

    report = relationship("MedicalReport", back_populates="metrics")
