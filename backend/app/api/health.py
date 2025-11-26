"""
Health check endpoints.
"""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas import HealthResponse
from app.core.config import settings
from app.models.database import get_db

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    Returns application status and basic info.
    """
    # Test database connection
    try:
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.utcnow()
    )
