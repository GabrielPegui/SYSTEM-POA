"""Health check endpoint.

Used by infrastructure (load balancers, orchestration) and by the frontend
to detect service availability. It must never depend on external resources
being available; the database status is reported without blocking.
"""

from fastapi import APIRouter

from app.core.config import settings
from app.database.session import database_status

router = APIRouter()


@router.get("/health", summary="Service health check")
def health_check() -> dict:
    """Return the service status and a non-blocking database indicator."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "database": database_status(),
    }
