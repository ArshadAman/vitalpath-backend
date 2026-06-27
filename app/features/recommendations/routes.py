from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.features.recommendations.schemas import RecommendationResponse
from app.features.recommendations.services import generate_recommendations

router = APIRouter(prefix="/recommendations", tags=["Recommendation Engine"])

@router.get("", response_model=RecommendationResponse)
def read_recommendations(user_id: int, db: Session = Depends(get_db)):
    """Retrieves lifestyle guidelines (diet/exercise) and test suggestions for user."""
    return generate_recommendations(db, user_id)
