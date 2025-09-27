from contextlib import asynccontextmanager
from typing import AsyncGenerator
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import get_settings


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


def _sanitize_database_url(db_url: str) -> str:
    """Convert to asyncpg scheme and drop unsupported params like sslmode/channel_binding."""
    parsed = urlparse(db_url)
    # Remove params not accepted by asyncpg.connect
    filtered_qs = [
        (k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in ("sslmode", "channel_binding")
    ]
    new_query = urlencode(filtered_qs, doseq=True)
    new_scheme = parsed.scheme.replace("postgresql", "postgresql+asyncpg")
    return urlunparse(parsed._replace(scheme=new_scheme, query=new_query))


# Create async engine
engine = create_async_engine(
    _sanitize_database_url(get_settings().DATABASE_URL),
    echo=get_settings().DEBUG,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"ssl": True},
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
