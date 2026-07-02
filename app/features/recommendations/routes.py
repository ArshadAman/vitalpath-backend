from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.features.auth.services import get_current_user
from app.features.auth.models import User
from app.features.recommendations.schemas import RecommendationResponse
from app.features.recommendations.services import generate_recommendations

router = APIRouter(prefix="/recommendations", tags=["Recommendation Engine"])

@router.get("", response_model=RecommendationResponse)
def read_recommendations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieves lifestyle guidelines (diet/exercise) and test suggestions for user."""
    return generate_recommendations(db, current_user.id)
