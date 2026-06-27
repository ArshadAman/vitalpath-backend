from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.features.tracking.schemas import (
    ActivityCreate, ActivityResponse, SleepCreate, SleepResponse,
    WeightCreate, WeightResponse, BPCreate, BPResponse
)
from app.features.tracking.services import (
    log_activity, get_activities, log_sleep, get_sleep_logs,
    log_weight, get_weight_logs, log_bp, get_bp_logs
)

router = APIRouter(prefix="/tracking", tags=["Lifestyle Tracking"])

@router.post("/activity", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
def record_activity(user_id: int, activity_data: ActivityCreate, db: Session = Depends(get_db)):
    """Logs steps, distance, and active minutes."""
    return log_activity(db, user_id, activity_data)

@router.get("/activity", response_model=List[ActivityResponse])
def read_activities(user_id: int, db: Session = Depends(get_db)):
    """Retrieves activities logged by user."""
    return get_activities(db, user_id)

@router.post("/sleep", response_model=SleepResponse, status_code=status.HTTP_201_CREATED)
def record_sleep(user_id: int, sleep_data: SleepCreate, db: Session = Depends(get_db)):
    """Logs daily sleep logs."""
    return log_sleep(db, user_id, sleep_data)

@router.get("/sleep", response_model=List[SleepResponse])
def read_sleep_logs(user_id: int, db: Session = Depends(get_db)):
    """Retrieves sleep history logs."""
    return get_sleep_logs(db, user_id)

@router.post("/weight", response_model=WeightResponse, status_code=status.HTTP_201_CREATED)
def record_weight(user_id: int, weight_data: WeightCreate, db: Session = Depends(get_db)):
    """Logs weight metric."""
    return log_weight(db, user_id, weight_data)

@router.get("/weight", response_model=List[WeightResponse])
def read_weight_logs(user_id: int, db: Session = Depends(get_db)):
    """Retrieves weight updates history."""
    return get_weight_logs(db, user_id)

@router.post("/bp", response_model=BPResponse, status_code=status.HTTP_201_CREATED)
def record_bp(user_id: int, bp_data: BPCreate, db: Session = Depends(get_db)):
    """Logs blood pressure measurement."""
    return log_bp(db, user_id, bp_data)

@router.get("/bp", response_model=List[BPResponse])
def read_bp_logs(user_id: int, db: Session = Depends(get_db)):
    """Retrieves blood pressure logs."""
    return get_bp_logs(db, user_id)
