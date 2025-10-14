"""
Database configuration and session management.
Uses SQLAlchemy with async support and Alembic for migrations.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

# Create async engine
if settings.TESTING:
    # Use in-memory SQLite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG,
    )
else:
    # Use PostgreSQL for production
    engine = create_async_engine(
        settings.sql_database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=settings.DEBUG,
        pool_pre_ping=True,
    )

# Create async session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


async def get_db():
    """
    Dependency for getting async database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables() -> None:
    """
    Create all database tables.
    In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """
    Drop all database tables.
    Used for testing.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)