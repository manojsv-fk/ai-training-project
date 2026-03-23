# filepath: market-research-platform/backend/main.py
# FastAPI application entry point.
# Registers all API routers, initializes the database, starts LlamaIndex,
# and starts the APScheduler background scheduler.

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import func, select

from config import settings
from database import init_db, AsyncSessionLocal
from core.llamaindex_engine import get_engine
from core.scheduler.jobs import start_scheduler, shutdown_scheduler, get_app_state
from api.routes import documents, chat, reports, trends, news

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle hooks."""
    # ── Startup ──────────────────────────────────────────────────────────
    logger.info("Starting Market Research Intelligence Platform...")

    # 1. Initialize database tables
    await init_db()
    logger.info("Database initialized.")

    # 2. Initialize LlamaIndex engine (PGVectorStore, index)
    try:
        engine = get_engine()
        logger.info("LlamaIndex engine ready.")
    except Exception as e:
        logger.error(f"LlamaIndex initialization failed: {e}")
        logger.warning("Application will start but LLM features will be unavailable.")

    # 3. Start background scheduler
    try:
        start_scheduler()
    except Exception as e:
        logger.warning(f"Scheduler failed to start: {e}")

    logger.info("Application startup complete.")
    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    logger.info("Shutting down...")
    shutdown_scheduler()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="Market Research Intelligence Platform",
    description="AI-powered market research aggregation, trend analysis, and Q&A.",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:3000",
        "http://frontend:3000",   # Docker internal
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(trends.router, prefix="/api/trends", tags=["trends"])
app.include_router(news.router, prefix="/api/news", tags=["news"])


@app.get("/api/status")
async def status():
    """Health check and system status endpoint consumed by the frontend StatusBar."""
    from models.document import Document

    app_state = get_app_state()

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(func.count(Document.id)))
            doc_count = result.scalar() or 0
    except Exception:
        doc_count = 0

    return {
        "doc_count": doc_count,
        "last_sync": app_state.get("last_news_sync"),
        "index_status": "ready",
    }


@app.get("/api/settings")
async def get_settings():
    """Return current application settings (read-only sensitive fields masked)."""
    provider = settings.llm_provider
    llm_model = settings.gemini_llm_model if provider == "gemini" else settings.openai_llm_model
    embed_model = settings.gemini_embedding_model if provider == "gemini" else settings.openai_embedding_model

    return {
        "llm_provider": provider,
        "llm_model": llm_model,
        "embedding_model": embed_model,
        "news_topics": settings.news_topics,
        "news_sync_interval_minutes": settings.news_sync_interval_minutes,
        "weekly_brief_cron": settings.weekly_brief_cron,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
        "retrieval_top_k": settings.retrieval_top_k,
        "max_upload_size_mb": settings.max_upload_size_mb,
        "api_keys_configured": {
            "gemini": bool(settings.gemini_api_key),
            "openai": bool(settings.openai_api_key),
            "llama_cloud": bool(settings.llama_cloud_api_key),
            "newsapi": bool(settings.newsapi_key),
        },
    }


@app.patch("/api/settings")
async def update_settings(payload: dict):
    """Update mutable application settings (in-memory only for POC)."""
    updatable = {
        "news_topics": str,
        "news_sync_interval_minutes": int,
        "weekly_brief_cron": str,
        "retrieval_top_k": int,
    }

    updated = {}
    for key, value in payload.items():
        if key in updatable:
            setattr(settings, key, updatable[key](value))
            updated[key] = value

    return {"updated": updated}


# ── Dev entrypoint ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
