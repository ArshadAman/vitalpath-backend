from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import Base, engine
from app.core.monitoring import MetricsMiddleware, metrics_route

# Import feature routes
from app.features.auth.routes import router as auth_router
from app.features.profile.routes import router as profile_router
from app.features.timeline.routes import router as timeline_router
from app.features.reports.routes import router as reports_router
from app.features.tracking.routes import router as tracking_router
from app.features.voice.routes import router as voice_router
from app.features.score.routes import router as score_router
from app.features.recommendations.routes import router as recommendations_router
from app.features.goals.routes import router as goals_router
from app.features.notifications.routes import router as notifications_router

# Configure global logger
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events manager for the application."""
    if settings.is_local:
        # Create database tables automatically in local mode
        Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="VitalPath API - Personal Health Navigation System Backend",
    version="1.0.0",
    lifespan=lifespan
)

# Register Prometheus metric-capturing middleware
app.add_middleware(MetricsMiddleware)

# Prometheus scraper endpoint
app.add_route("/metrics", metrics_route)

# Register API endpoint routes
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(timeline_router)
app.include_router(reports_router)
app.include_router(tracking_router)
app.include_router(voice_router)
app.include_router(score_router)
app.include_router(recommendations_router)
app.include_router(goals_router)
app.include_router(notifications_router)

@app.get("/")
def read_root():
    """Service health-check root path."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.APP_ENV
    }
