"""
Redis configuration and connection management.
Provides caching and session storage capabilities.
"""

import redis.asyncio as redis
from typing import Optional

from app.core.config import settings

# Global Redis client
redis_client: Optional[redis.Redis] = None


async def init_redis() -> None:
    """
    Initialize Redis connection.
    """
    global redis_client

    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True,
        )

        # Test connection
        await redis_client.ping()
        print("✅ Redis connection established")

    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        redis_client = None


async def get_redis() -> Optional[redis.Redis]:
    """
    Get Redis client instance.
    """
    return redis_client


async def close_redis() -> None:
    """
    Close Redis connection.
    """
    global redis_client

    if redis_client:
        await redis_client.close()
        redis_client = None