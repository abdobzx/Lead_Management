"""
Health check endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import time

from app.core.database import get_db

router = APIRouter()


@router.get("/")
async def health_check():
    """
    Basic health check endpoint.
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "lead-management-api"
    }


@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """
    Detailed health check including database connectivity.
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {}
    }

    # Database check
    try:
        await db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Redis check (if available)
    try:
        from app.core.redis import get_redis
        redis_client = await get_redis()
        if redis_client:
            await redis_client.ping()
            health_status["checks"]["redis"] = "healthy"
        else:
            health_status["checks"]["redis"] = "not configured"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    return health_status