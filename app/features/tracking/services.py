from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.features.tracking.models import ActivityLog, SleepLog, WeightLog, BPLog
from app.features.tracking.schemas import ActivityCreate, SleepCreate, WeightCreate, BPCreate

def log_activity(db: Session, user_id: int, activity_data: ActivityCreate) -> ActivityLog:
    """Logs user daily activities."""
    log = ActivityLog(user_id=user_id, **activity_data.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_activities(db: Session, user_id: int) -> List[ActivityLog]:
    """Retrieves logged activities for a user."""
    return db.query(ActivityLog).filter(ActivityLog.user_id == user_id).order_by(ActivityLog.date.desc()).all()

def log_sleep(db: Session, user_id: int, sleep_data: SleepCreate) -> SleepLog:
    """Logs sleep stats."""
    log = SleepLog(user_id=user_id, **sleep_data.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_sleep_logs(db: Session, user_id: int) -> List[SleepLog]:
    """Retrieves logged sleep states."""
    return db.query(SleepLog).filter(SleepLog.user_id == user_id).order_by(SleepLog.date.desc()).all()

def log_weight(db: Session, user_id: int, weight_data: WeightCreate) -> WeightLog:
    """Logs daily/weekly body weight update."""
    log = WeightLog(user_id=user_id, **weight_data.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_weight_logs(db: Session, user_id: int) -> List[WeightLog]:
    """Retrieves body weight logs."""
    return db.query(WeightLog).filter(WeightLog.user_id == user_id).order_by(WeightLog.date.desc()).all()

def log_bp(db: Session, user_id: int, bp_data: BPCreate) -> BPLog:
    """Logs a manual blood pressure reading."""
    log = BPLog(user_id=user_id, **bp_data.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_bp_logs(db: Session, user_id: int) -> List[BPLog]:
    """Retrieves blood pressure logs."""
    return db.query(BPLog).filter(BPLog.user_id == user_id).order_by(BPLog.date.desc()).all()
