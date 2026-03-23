# filepath: market-research-platform/backend/database.py
# SQLAlchemy async engine and session factory.
# Also exposes the declarative Base class for all ORM models.
# Used by API routes via the get_db() dependency injector.

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import settings

# ── Async engine ──────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.database_url,
    echo=(settings.app_env == "development"),
    pool_pre_ping=True,
)

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ── Base class for ORM models ─────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Dependency injector ───────────────────────────────────────────────────────
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


# ── Database initialization ───────────────────────────────────────────────────
async def init_db():
    """
    Create all tables on startup (dev/POC only).
    Import all models here so Base.metadata is populated before create_all.
    """
    # Import models to register them with Base.metadata
    import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
