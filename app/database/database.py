from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import get_settings


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Create async engine
engine = create_async_engine(
    get_settings().DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=get_settings().DEBUG,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"ssl": True}
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def lifespan(app):
    """Application lifespan manager for database connections."""
    # Startup
    print("Starting up Cheetah API...")
    
    # Test database connection
    try:
        async with engine.begin() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        print("Database connection established successfully")
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise
    
    yield
    
    # Shutdown
    print("Shutting down Cheetah API...")
    await engine.dispose()
