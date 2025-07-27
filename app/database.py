"""
Database configuration and connection management
"""

import redis.asyncio as redis
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

from app.config import settings

# SQLAlchemy setup
engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.is_development,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
)

async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# Metadata for migrations
metadata = MetaData()

# Redis setup
redis_client = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_redis() -> redis.Redis:
    """
    Get Redis client
    """
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            retry_on_timeout=True,
        )
    return redis_client


async def init_database():
    """
    Initialize database tables
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_database():
    """
    Close database connections
    """
    await engine.dispose()
    if redis_client:
        await redis_client.close()


class DatabaseManager:
    """
    Database connection manager
    """
    
    def __init__(self):
        self.engine = engine
        self.session_maker = async_session_maker
        self.redis = None
    
    async def connect(self):
        """Connect to databases"""
        self.redis = await get_redis()
        
        # Test connection
        try:
            await self.redis.ping()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")
    
    async def disconnect(self):
        """Disconnect from databases"""
        await close_database()
    
    async def health_check(self) -> dict:
        """Check database health"""
        status = {"database": "unknown", "redis": "unknown"}
        
        try:
            async with self.session_maker() as session:
                await session.execute("SELECT 1")
                status["database"] = "healthy"
        except Exception as e:
            status["database"] = f"unhealthy: {str(e)}"
        
        try:
            await self.redis.ping()
            status["redis"] = "healthy"
        except Exception as e:
            status["redis"] = f"unhealthy: {str(e)}"
        
        return status


# Global database manager instance
db_manager = DatabaseManager()