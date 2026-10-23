"""Health check API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas import HealthResponse


router = APIRouter(prefix="/health", tags=["health"])
settings = get_settings()


@router.get("", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """
    Health check endpoint.
    Verifies database connectivity and returns service status.
    """
    db_status = "disconnected"
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "error"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        version=settings.app_version,
        environment=settings.environment,
        database=db_status,
    )


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Kubernetes readiness probe endpoint.
    Returns 200 if service is ready to accept traffic.
    """
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return {"status": "not ready"}


@router.get("/live")
async def liveness_check() -> dict:
    """
    Kubernetes liveness probe endpoint.
    Returns 200 if service is alive.
    """
    return {"status": "alive"}