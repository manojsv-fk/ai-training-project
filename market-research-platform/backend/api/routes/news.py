# filepath: market-research-platform/backend/api/routes/news.py
# REST endpoints for manual news ingestion control.

import logging

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_session, get_llama_engine
from config import settings
from core.llamaindex_engine import LlamaIndexEngine
from core.ingestion.news_ingestion import run_news_sync
from core.scheduler.jobs import get_app_state

logger = logging.getLogger(__name__)

router = APIRouter()


class NewsConfigUpdate(BaseModel):
    topics: str | None = None
    sync_interval_minutes: int | None = None


@router.post("/sync")
async def trigger_news_sync(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
    engine: LlamaIndexEngine = Depends(get_llama_engine),
):
    """
    Manually trigger a news article sync from NewsAPI and Google News RSS.
    Runs synchronously for POC (could be backgrounded for production).
    """
    try:
        result = await run_news_sync(engine, db)

        # Update app state
        from datetime import datetime, timezone
        app_state = get_app_state()
        app_state["last_news_sync"] = datetime.now(timezone.utc).isoformat()

        return {
            "status": "complete",
            **result,
        }
    except Exception as e:
        logger.error(f"Manual news sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"News sync failed: {str(e)}")


@router.get("/config")
async def get_news_config():
    """Return current news ingestion configuration (topics, interval)."""
    app_state = get_app_state()
    return {
        "topics": settings.news_topics,
        "sync_interval_minutes": settings.news_sync_interval_minutes,
        "last_sync": app_state.get("last_news_sync"),
    }


@router.patch("/config")
async def update_news_config(body: NewsConfigUpdate):
    """
    Update news ingestion topics and/or sync interval.
    Note: For POC, this updates the in-memory settings only (not .env file).
    Changes are lost on restart.
    """
    if body.topics is not None:
        settings.news_topics = body.topics

    if body.sync_interval_minutes is not None:
        if body.sync_interval_minutes < 5:
            raise HTTPException(status_code=400, detail="Minimum interval is 5 minutes.")
        settings.news_sync_interval_minutes = body.sync_interval_minutes

        # Reschedule the news sync job with the new interval
        try:
            from core.scheduler.jobs import scheduler
            from apscheduler.triggers.interval import IntervalTrigger

            scheduler.reschedule_job(
                "news_sync",
                trigger=IntervalTrigger(minutes=body.sync_interval_minutes),
            )
            logger.info(f"Rescheduled news sync to every {body.sync_interval_minutes} minutes")
        except Exception as e:
            logger.warning(f"Failed to reschedule news sync: {e}")

    return {
        "topics": settings.news_topics,
        "sync_interval_minutes": settings.news_sync_interval_minutes,
        "updated": True,
    }
