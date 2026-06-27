import logging
from app.celery_app import celery
from app.core.database import SessionLocal
from app.features.score.services import calculate_health_metrics
from app.features.auth.models import User

logger = logging.getLogger(__name__)

@celery.task(name="score.periodic_recalculate")
def recalculate_all_scores_task():
    """Asynchronous/periodic task to recalculate health scores for active users."""
    logger.info("Starting periodic recalculation of health scores...")
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        for user in users:
            try:
                calculate_health_metrics(db, user.id)
                logger.info(f"Recalculated health score for user {user.id}")
            except Exception as ex:
                logger.error(f"Failed to calculate health score for user {user.id}: {ex}")
        return True
    except Exception as e:
        logger.exception(f"Error in periodic score recalculation: {e}")
        return False
    finally:
        db.close()
