from celery import Celery
from app.core.config import settings

celery = Celery(
    "vitalpath",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Auto-discover tasks from feature directories
celery.autodiscover_tasks([
    "app.features.auth",
    "app.features.reports",
    "app.features.voice",
    "app.features.score",
    "app.features.goals",
    "app.features.notifications"
])

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True
)
