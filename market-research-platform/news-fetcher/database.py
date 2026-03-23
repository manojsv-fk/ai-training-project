# filepath: market-research-platform/news-fetcher/database.py
# SQLAlchemy async engine and session factory.
# Shares the same PostgreSQL database as the main backend service.

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import settings

# -- Async engine -----------------------------------------------------------
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)

# -- Session factory --------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# -- Base class for ORM models ----------------------------------------------
class Base(DeclarativeBase):
    pass


# -- Dependency injector ----------------------------------------------------
async def get_db() -> AsyncSession:
    """FastAPI dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# -- Database initialization ------------------------------------------------
async def init_db():
    """
    Create all tables on startup (dev/POC only).
    Import models here so Base.metadata is populated before create_all.
    """
    import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
