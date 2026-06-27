from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.features.score.models import HealthScoreLog
from app.features.profile.services import get_health_profile
from app.features.tracking.models import ActivityLog, SleepLog
from app.features.reports.models import ExtractedMetric

def calculate_health_metrics(db: Session, user_id: int) -> HealthScoreLog:
    """Calculates user overall health score (0-100) and biological health age based on health data."""
    # 1. Fetch dependencies
    profile = get_health_profile(db, user_id)
    
    # Defaults
    actual_age = 30
    weight = 70.0
    smoking = "never"
    alcohol = "none"
    exercise = "rarely"
    
    if profile:
        if profile.date_of_birth:
            actual_age = (datetime.utcnow() - profile.date_of_birth).days // 365
        if profile.weight:
            weight = profile.weight
        smoking = profile.smoking_status
        alcohol = profile.alcohol_consumption
        exercise = profile.exercise_frequency

    # Fetch recent lifestyle tracking
    recent_activity = db.query(ActivityLog).filter(ActivityLog.user_id == user_id).order_by(ActivityLog.date.desc()).first()
    recent_sleep = db.query(SleepLog).filter(SleepLog.user_id == user_id).order_by(SleepLog.date.desc()).first()
    
    steps = recent_activity.steps if recent_activity else 5000
    sleep_hours = recent_sleep.duration_hours if recent_sleep else 7.0

    # Fetch recent medical reports metrics
    hb_a1c = db.query(ExtractedMetric).join(ExtractedMetric.report).filter(
        ExtractedMetric.test_name == "HbA1c"
    ).order_by(ExtractedMetric.test_date.desc()).first()

    # 2. Algorithm Logic
    base_score = 80
    health_age_offset = 0

    # Step impact
    if steps > 10000:
        base_score += 5
        health_age_offset -= 1
    elif steps < 3000:
        base_score -= 10
        health_age_offset += 2

    # Sleep impact
    if 7.0 <= sleep_hours <= 9.0:
        base_score += 5
        health_age_offset -= 1
    elif sleep_hours < 6.0:
        base_score -= 5
        health_age_offset += 1

    # Substance impact
    if smoking == "active":
        base_score -= 15
        health_age_offset += 5
    if alcohol == "regular":
        base_score -= 10
        health_age_offset += 3

    # Medical report impact (HbA1c)
    if hb_a1c:
        if hb_a1c.value > 6.5: # Diabetes range
            base_score -= 15
            health_age_offset += 4
        elif hb_a1c.value < 5.7: # Normal range
            base_score += 5

    # Clamp scores
    final_score = max(0, min(100, base_score))
    final_health_age = max(18, actual_age + health_age_offset)

    factors = {
        "steps_analyzed": steps,
        "sleep_hours_analyzed": sleep_hours,
        "smoking_status": smoking,
        "alcohol_consumption": alcohol,
        "hba1c_level": hb_a1c.value if hb_a1c else None,
        "actual_age": actual_age
    }

    # 3. Save log to DB
    score_log = HealthScoreLog(
        user_id=user_id,
        score=final_score,
        health_age=final_health_age,
        factors=factors
    )
    db.add(score_log)
    db.commit()
    db.refresh(score_log)
    return score_log

def get_latest_health_score(db: Session, user_id: int) -> Optional[HealthScoreLog]:
    """Queries the database for the most recent health score log entry."""
    return db.query(HealthScoreLog).filter(HealthScoreLog.user_id == user_id).order_by(HealthScoreLog.created_at.desc()).first()
