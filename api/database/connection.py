"""Database connection and session management."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from api.config import config

# Create async engine
engine = create_async_engine(
    config.DATABASE_URL,
    echo=config.ENVIRONMENT == 'development',
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()


async def get_db():
    """Dependency for FastAPI to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database (create tables).
    
    Imports all models to ensure they're registered with Base.metadata.
    """
    # Import models to register them
    from api.database.models import Character  # noqa: F401
    from api.database.feedback_models import RoutingFeedback  # noqa: F401
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connection."""
    await engine.dispose()
