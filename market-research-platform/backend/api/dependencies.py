# filepath: market-research-platform/backend/api/dependencies.py
# Shared FastAPI dependency functions injected into route handlers.
# Provides database sessions and the LlamaIndex engine.

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from core.llamaindex_engine import LlamaIndexEngine, get_engine


async def get_session(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    """Pass-through dependency for the async DB session."""
    return db


def get_llama_engine(engine: LlamaIndexEngine = Depends(get_engine)) -> LlamaIndexEngine:
    """Provides the singleton LlamaIndex engine to route handlers."""
    return engine
