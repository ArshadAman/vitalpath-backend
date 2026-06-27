from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.features.goals.models import Goal
from app.features.goals.schemas import GoalCreate, GoalUpdate
from app.features.tracking.models import WeightLog, SleepLog

def get_user_goals(db: Session, user_id: int) -> List[Goal]:
    """Retrieves all health goals created by a user."""
    return db.query(Goal).filter(Goal.user_id == user_id).all()

def create_goal(db: Session, user_id: int, goal_data: GoalCreate) -> Goal:
    """Registers a new health goal."""
    db_goal = Goal(
        user_id=user_id,
        **goal_data.model_dump()
    )
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal

def update_goal(db: Session, goal_id: int, update_data: GoalUpdate) -> Optional[Goal]:
    """Manually updates a goal status/values."""
    db_goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not db_goal:
        return None
        
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(db_goal, key, value)
        
    db.commit()
    db.refresh(db_goal)
    return db_goal

def evaluate_goal_progress(db: Session, user_id: int):
    """Automatically scans database and syncs goals status with the latest tracking logs."""
    goals = db.query(Goal).filter(Goal.user_id == user_id, Goal.status == "active").all()
    for goal in goals:
        if goal.goal_type == "lose_weight":
            latest_weight = db.query(WeightLog).filter(WeightLog.user_id == user_id).order_by(WeightLog.date.desc()).first()
            if latest_weight:
                goal.current_value = latest_weight.weight_kg
                # Check if target met (weight loss usually target is lower than start)
                if goal.current_value <= goal.target_value:
                    goal.status = "completed"
                    
        elif goal.goal_type == "improve_sleep":
            latest_sleep = db.query(SleepLog).filter(SleepLog.user_id == user_id).order_by(SleepLog.date.desc()).first()
            if latest_sleep:
                goal.current_value = latest_sleep.duration_hours
                if goal.current_value >= goal.target_value:
                    goal.status = "completed"
                    
        if goal.target_date < datetime.utcnow() and goal.status == "active":
            goal.status = "failed"
            
    db.commit()
