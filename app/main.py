"""
Lead Management AI System - FastAPI Application
A comprehensive AI-powered lead management system with multi-agent architecture.

Author: Abderrahman
GitHub: https://github.com/abdobzx
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog
import time
from typing import Any

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import create_tables
from app.core.redis import init_redis

# Setup structured logging
setup_logging()

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    logger.info("Starting Lead Management System")

    # Startup
    try:
        await create_tables()
        await init_redis()
        logger.info("Application startup complete")
    except Exception as e:
        logger.error("Startup failed", error=str(e))
        raise

    yield

    # Shutdown
    logger.info("Shutting down Lead Management System")


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Set up CORS
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Add trusted host middleware
    if not settings.DEBUG:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS,
        )

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()

        # Log request
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            client_ip=getattr(request.client, 'host', 'unknown') if request.client else 'unknown',
        )

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log response
            logger.info(
                "Request completed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time=f"{process_time:.3f}s",
            )

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "Request failed",
                method=request.method,
                url=str(request.url),
                error=str(e),
                process_time=f"{process_time:.3f}s",
            )
            raise

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception",
            error=str(exc),
            url=str(request.url),
            method=request.method,
        )

        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # Include API routers
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint for monitoring."""
        return {
            "status": "healthy",
            "version": settings.VERSION,
            "timestamp": time.time(),
        }

    # Detailed health check endpoint
    @app.get("/health/detailed")
    async def detailed_health_check():
        """Detailed health check including database and redis connectivity."""
        from app.core.database import AsyncSessionLocal
        
        health_status = {
            "status": "healthy",
            "version": settings.VERSION,
            "timestamp": time.time(),
            "checks": {}
        }

        # Database check
        try:
            async with AsyncSessionLocal() as db:
                from sqlalchemy import text
                await db.execute(text("SELECT 1"))
            health_status["checks"]["database"] = "healthy"
        except Exception as e:
            health_status["checks"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"

        # Redis check
        try:
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

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "message": "Lead Management AI System API",
            "version": settings.VERSION,
            "docs": "/docs",
            "health": "/health",
        }

    return app


# Create the FastAPI application instance
app = create_application()