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
from app.features.auth.services import get_current_user
from app.features.auth.models import User
from app.features.score.services import calculate_health_metrics

router = APIRouter(prefix="/tracking", tags=["Lifestyle Tracking"])

@router.post("/activity", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
def record_activity(activity_data: ActivityCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Logs steps, distance, and active minutes."""
    res = log_activity(db, current_user.id, activity_data)
    calculate_health_metrics(db, current_user.id)
    return res

@router.get("/activity", response_model=List[ActivityResponse])
def read_activities(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieves activities logged by user."""
    return get_activities(db, current_user.id)

@router.post("/sleep", response_model=SleepResponse, status_code=status.HTTP_201_CREATED)
def record_sleep(sleep_data: SleepCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Logs daily sleep logs."""
    res = log_sleep(db, current_user.id, sleep_data)
    calculate_health_metrics(db, current_user.id)
    return res

@router.get("/sleep", response_model=List[SleepResponse])
def read_sleep_logs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieves sleep history logs."""
    return get_sleep_logs(db, current_user.id)

@router.post("/weight", response_model=WeightResponse, status_code=status.HTTP_201_CREATED)
def record_weight(weight_data: WeightCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Logs weight metric."""
    res = log_weight(db, current_user.id, weight_data)
    calculate_health_metrics(db, current_user.id)
    return res

@router.get("/weight", response_model=List[WeightResponse])
def read_weight_logs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieves weight updates history."""
    return get_weight_logs(db, current_user.id)

@router.post("/bp", response_model=BPResponse, status_code=status.HTTP_201_CREATED)
def record_bp(bp_data: BPCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Logs blood pressure measurement."""
    res = log_bp(db, current_user.id, bp_data)
    calculate_health_metrics(db, current_user.id)
    return res

@router.get("/bp", response_model=List[BPResponse])
def read_bp_logs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieves blood pressure logs."""
    return get_bp_logs(db, current_user.id)
