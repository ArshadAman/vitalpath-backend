from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.features.goals.schemas import GoalResponse, GoalCreate, GoalUpdate
from app.features.goals.services import get_user_goals, create_goal, update_goal, evaluate_goal_progress

router = APIRouter(prefix="/goals", tags=["Health Goals"])

@router.get("", response_model=List[GoalResponse])
def read_goals(user_id: int, db: Session = Depends(get_db)):
    """Retrieves all goals for the user, triggering automatic evaluations first."""
    evaluate_goal_progress(db, user_id)
    return get_user_goals(db, user_id)

@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def add_goal(user_id: int, goal_data: GoalCreate, db: Session = Depends(get_db)):
    """Creates a new health goal."""
    return create_goal(db, user_id, goal_data)

@router.put("/{goal_id}", response_model=GoalResponse)
def modify_goal(goal_id: int, update_data: GoalUpdate, db: Session = Depends(get_db)):
    """Updates status or values for health goal."""
    db_goal = update_goal(db, goal_id, update_data)
    if not db_goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return db_goal
