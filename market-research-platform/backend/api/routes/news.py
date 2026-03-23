# filepath: market-research-platform/backend/api/routes/news.py
# REST endpoints for manual news ingestion control.
# When NEWS_FETCHER_URL is configured, sync and article requests are proxied
# to the news-fetcher microservice. Otherwise, falls back to local ingestion.

import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_session, get_llama_engine
from config import settings
from core.llamaindex_engine import LlamaIndexEngine
from core.ingestion.news_ingestion import run_news_sync
from core.scheduler.jobs import get_app_state

logger = logging.getLogger(__name__)

router = APIRouter()

# Timeout for internal service calls (seconds)
_SERVICE_TIMEOUT = 30.0


class NewsConfigUpdate(BaseModel):
    topics: str | None = None
    sync_interval_minutes: int | None = None


async def _proxy_get(path: str, params: dict | None = None) -> dict:
    """Make a GET request to the news-fetcher microservice."""
    url = f"{settings.news_fetcher_url}{path}"
    async with httpx.AsyncClient(timeout=_SERVICE_TIMEOUT) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


async def _proxy_post(path: str, json_body: dict | None = None) -> dict:
    """Make a POST request to the news-fetcher microservice."""
    url = f"{settings.news_fetcher_url}{path}"
    async with httpx.AsyncClient(timeout=_SERVICE_TIMEOUT) as client:
        resp = await client.post(url, json=json_body or {})
        resp.raise_for_status()
        return resp.json()


@router.post("/sync")
async def trigger_news_sync(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
    engine: LlamaIndexEngine = Depends(get_llama_engine),
):
    """
    Manually trigger a news article sync.
    If NEWS_FETCHER_URL is set, proxies the request to the news-fetcher microservice.
    Otherwise, runs the local ingestion pipeline.
    """
    # ── Proxy to news-fetcher microservice if configured ──────────────────
    if settings.news_fetcher_url:
        try:
            result = await _proxy_post("/fetch")
            # Update app state with the sync time
            from datetime import datetime, timezone
            app_state = get_app_state()
            app_state["last_news_sync"] = datetime.now(timezone.utc).isoformat()
            return {"status": "complete", "source": "news_fetcher", **result}
        except httpx.ConnectError:
            logger.warning(
                "News fetcher service unreachable, falling back to local sync"
            )
            # Fall through to local sync
        except Exception as e:
            logger.warning(
                f"News fetcher proxy failed ({e}), falling back to local sync"
            )
            # Fall through to local sync

    # ── Local fallback ────────────────────────────────────────────────────
    try:
        result = await run_news_sync(engine, db)

        from datetime import datetime, timezone
        app_state = get_app_state()
        app_state["last_news_sync"] = datetime.now(timezone.utc).isoformat()

        return {
            "status": "complete",
            "source": "local",
            **result,
        }
    except Exception as e:
        logger.error(f"Manual news sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"News sync failed: {str(e)}")


@router.get("/articles")
async def get_articles(
    category: str | None = Query(None, description="Filter by news category"),
    limit: int = Query(50, ge=1, le=200, description="Max articles to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """
    Retrieve articles from the news-fetcher microservice.
    Only available when NEWS_FETCHER_URL is configured; returns 404 otherwise.
    """
    if not settings.news_fetcher_url:
        raise HTTPException(
            status_code=404,
            detail="News fetcher service not configured. Articles are stored locally in the documents table.",
        )

    try:
        params = {"limit": limit, "offset": offset}
        if category:
            params["category"] = category
        result = await _proxy_get("/articles", params=params)
        return result
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503, detail="News fetcher service is unreachable"
        )
    except Exception as e:
        logger.error(f"Failed to fetch articles from news-fetcher: {e}")
        raise HTTPException(status_code=502, detail=f"News fetcher error: {str(e)}")


@router.get("/config")
async def get_news_config():
    """Return current news ingestion configuration (topics, interval)."""
    app_state = get_app_state()
    return {
        "topics": settings.news_topics,
        "sync_interval_minutes": settings.news_sync_interval_minutes,
        "last_sync": app_state.get("last_news_sync"),
        "news_fetcher_url": settings.news_fetcher_url or None,
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

        # Only reschedule local job if news-fetcher is NOT configured
        if not settings.news_fetcher_url:
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
