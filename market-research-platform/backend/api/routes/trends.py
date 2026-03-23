# filepath: market-research-platform/backend/api/routes/trends.py
# REST endpoints for market trend identification.

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_session, get_llama_engine
from core.llamaindex_engine import LlamaIndexEngine
from core.query.summary_engine import SummaryEngine
from models.trend import Trend

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def list_trends(
    time_range_days: int | None = Query(default=None),
    topic: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_session),
):
    """
    Return identified trends, optionally filtered by time range or topic.
    Sorted by confidence_score descending.
    """
    query = select(Trend).order_by(Trend.confidence_score.desc())

    # Filter by time range
    if time_range_days:
        cutoff = datetime.now(timezone.utc) - timedelta(days=time_range_days)
        query = query.where(Trend.identified_at >= cutoff)

    # Filter by topic (search in tags JSON field or title)
    if topic:
        search_term = f"%{topic}%"
        query = query.where(Trend.title.ilike(search_term))

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Limit results
    query = query.limit(limit)
    result = await db.execute(query)
    trends = result.scalars().all()

    return {
        "trends": [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "confidence_score": t.confidence_score,
                "tags": t.tags,
                "source_document_ids": t.source_document_ids,
                "identified_at": t.identified_at.isoformat(),
            }
            for t in trends
        ],
        "total": total,
    }


@router.post("/analyze")
async def trigger_trend_analysis(
    background_tasks: BackgroundTasks,
    document_ids: list[int] | None = Query(default=None),
    db: AsyncSession = Depends(get_session),
    engine: LlamaIndexEngine = Depends(get_llama_engine),
):
    """
    Trigger a fresh cross-document trend identification run.
    For POC, runs synchronously and returns results.
    """
    summary_engine = SummaryEngine(engine)

    try:
        trend_dicts = await summary_engine.identify_trends(
            document_ids=document_ids,
        )

        # Save trends to DB
        saved_trends = []
        for td in trend_dicts:
            trend = Trend(
                title=td.get("title", "Untitled"),
                description=td.get("description", ""),
                confidence_score=td.get("confidence_score", 0.5),
                supporting_chunk_ids=td.get("supporting_chunk_ids", []),
                source_document_ids=td.get("source_document_ids", []),
                tags=td.get("tags", []),
            )
            db.add(trend)
            saved_trends.append(trend)

        await db.commit()

        # Refresh to get IDs
        for trend in saved_trends:
            await db.refresh(trend)

        return {
            "status": "complete",
            "trends_identified": len(saved_trends),
            "trends": [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "confidence_score": t.confidence_score,
                    "tags": t.tags,
                    "identified_at": t.identified_at.isoformat(),
                }
                for t in saved_trends
            ],
        }

    except Exception as e:
        logger.error(f"Trend analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")
