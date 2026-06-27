from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from datetime import datetime
from app.core.database import Base

class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Personal Info
    name = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    blood_group = Column(String, nullable=True)

    # Health History Flags
    has_diabetes = Column(String, default="no") # no, yes, family_history
    has_hypertension = Column(String, default="no")
    has_cholesterol = Column(String, default="no")
    has_liver_disease = Column(String, default="no")
    has_heart_disease = Column(String, default="no")

    # Family History Flags
    family_diabetes = Column(String, default="no")
    family_heart_disease = Column(String, default="no")
    family_hypertension = Column(String, default="no")
    family_cancer = Column(String, default="no")

    # Lifestyle
    smoking_status = Column(String, default="never") # never, former, active
    alcohol_consumption = Column(String, default="none") # none, occasional, regular
    diet_type = Column(String, default="mixed") # veg, non-veg, vegan
    exercise_frequency = Column(String, default="rarely") # rarely, 1-2 times/week, 3+ times/week

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
