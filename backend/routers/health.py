"""
Health check router.
Verifies system health and MongoDB connectivity.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from pymongo.errors import PyMongoError
from src.config import get_settings
from src.db.mongo import ping_database
from backend.schemas import HealthResponse


router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_system_health():
    """
    Ping MongoDB Atlas and report service health.
    """
    settings = get_settings()
    try:
        ping_res = ping_database()
        return HealthResponse(
            status="healthy" if ping_res.get("ok") else "degraded",
            database=ping_res.get("database", settings.MONGODB_DB_NAME),
            app_env=settings.APP_ENV,
            version="1.0.0",
            timestamp=datetime.now(timezone.utc),
        )
    except PyMongoError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "detail": f"Database connectivity check failed: {exc.__class__.__name__}",
                "code": "DATABASE_UNREACHABLE",
            },
        )
