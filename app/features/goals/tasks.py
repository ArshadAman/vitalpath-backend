import logging
from app.celery_app import celery
from app.core.database import SessionLocal
from app.features.goals.services import evaluate_goal_progress
from app.features.auth.models import User

logger = logging.getLogger(__name__)

@celery.task(name="goals.periodic_evaluate")
def evaluate_all_goals_task():
    """Celery background task to trigger goal progress updates for all active users."""
    logger.info("Executing periodic health goals evaluation...")
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        for user in users:
            try:
                evaluate_goal_progress(db, user.id)
            except Exception as ex:
                logger.error(f"Error evaluating goals for user {user.id}: {ex}")
        return True
    except Exception as e:
        logger.exception(f"Error in goals scheduler: {e}")
        return False
    finally:
        db.close()
