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
    age = Column(Integer, nullable=True)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    blood_group = Column(String, nullable=True)

    # Targets & Parameters
    water_target = Column(Integer, default=2000)
    sleep_target = Column(Float, default=8.0)
    calorie_target = Column(Integer, default=2000)
    allergies = Column(String, nullable=True)
    medications = Column(String, nullable=True)

    # SaaS SaaS parameters
    health_goal = Column(String, default="wellness") # weight_loss, muscle_gain, cardiovascular, stress, longevity, wellness
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)

    # Health History Flags
    has_diabetes = Column(String, default="no")
    has_hypertension = Column(String, default="no")
    has_cholesterol = Column(String, default="no")
    has_liver_disease = Column(String, default="no")
    has_heart_disease = Column(String, default="no")
    has_stroke = Column(String, default="no")

    # Family History Flags
    family_diabetes = Column(String, default="no")
    family_heart_disease = Column(String, default="no")
    family_hypertension = Column(String, default="no")
    family_cancer = Column(String, default="no")

    # Lifestyle
    smoking_status = Column(String, default="none") 
    alcohol_consumption = Column(String, default="none") 
    diet_type = Column(String, default="balanced") 
    exercise_frequency = Column(String, default="active") 

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Properties mapping SQLAlchemy columns to JSON fields expected by frontend
    @property
    def bloodGroup(self):
        return self.blood_group

    @property
    def waterTarget(self):
        return self.water_target

    @property
    def sleepTarget(self):
        return self.sleep_target

    @property
    def calorieTarget(self):
        return self.calorie_target

    @property
    def healthGoal(self):
        return self.health_goal

    @property
    def emergencyContactName(self):
        return self.emergency_contact_name

    @property
    def emergencyContactPhone(self):
        return self.emergency_contact_phone

    @property
    def diabetes(self) -> bool:
        return self.has_diabetes == "yes"

    @property
    def hypertension(self) -> bool:
        return self.has_hypertension == "yes"

    @property
    def heartDisease(self) -> bool:
        return self.has_heart_disease == "yes"

    @property
    def strokeHistory(self) -> bool:
        return self.has_stroke == "yes"

    @property
    def smoking(self):
        return self.smoking_status

    @property
    def activity(self):
        return self.exercise_frequency

    @property
    def diet(self):
        return self.diet_type
