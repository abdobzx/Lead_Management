"""
Main API router for version 1 endpoints.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, leads, analytics, health

api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)

# Include all endpoint routers
api_router.include_router(
    leads.router,
    prefix="/leads",
    tags=["leads"]
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"]
)

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)