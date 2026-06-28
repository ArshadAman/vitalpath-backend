from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.features.score.schemas import HealthScoreResponse
from app.features.score.services import get_latest_health_score, calculate_health_metrics
from app.features.auth.services import get_current_user
from app.features.auth.models import User

router = APIRouter(prefix="/score", tags=["Health Score Engine"])

@router.get("/latest", response_model=HealthScoreResponse)
def read_latest_score(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetches the latest health score log entry for the user."""
    score_log = get_latest_health_score(db, current_user.id)
    if not score_log:
        raise HTTPException(status_code=404, detail="Health score log not found. Calculate one first.")
    return score_log

@router.post("/calculate", response_model=HealthScoreResponse)
def compute_health_metrics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Runs calculation engine and registers a new score log."""
    return calculate_health_metrics(db, current_user.id)
