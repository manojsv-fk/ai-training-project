# filepath: market-research-platform/news-fetcher/main.py
# FastAPI application for the Economic Times news-fetcher microservice.
# Scrapes ET India RSS feeds, stores articles in the shared PostgreSQL DB,
# and indexes them into the shared PGVectorStore for the main backend to query.

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Depends
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from llama_index.core import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import AsyncSessionLocal, init_db, get_db
from engine import NewsIndexEngine
from models import Document, SourceType
from scrapers import EconomicTimesScraper

# -- Logging ----------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("news-fetcher")

# -- Fetch statistics -------------------------------------------------------
_fetch_stats: dict[str, Any] = {
    "last_fetch_time": None,
    "last_fetch_articles": 0,
    "total_fetches": 0,
    "total_articles_ingested": 0,
    "errors": [],
}


# ---------------------------------------------------------------------------
# Core news-fetching logic (uses EconomicTimesScraper)
# ---------------------------------------------------------------------------

async def run_news_fetch(engine: NewsIndexEngine, db: AsyncSession) -> dict:
    """
    Fetch news from Economic Times via RSS feeds + full article scraping,
    store in the documents table, and index into the vector store.
    """
    categories = [c.strip() for c in settings.news_categories.split(",") if c.strip()]

    scraper = EconomicTimesScraper(categories=categories)
    articles = await scraper.fetch_articles(max_per_category=15)

    total_fetched = len(articles)
    ingested = 0
    skipped = 0

    splitter = SentenceSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    for article in articles:
        url = article.get("url", "")
        title = article.get("title", "").strip()
        if not url or not title:
            continue

        # Check for duplicate by original_url
        result = await db.execute(
            select(Document).where(Document.original_url == url)
        )
        if result.scalar_one_or_none():
            skipped += 1
            continue

        content_text = article.get("content", "") or article.get("summary", "")
        category = article.get("category", "")
        published_at = ""
        if article.get("published_at"):
            published_at = article["published_at"].isoformat() if hasattr(article["published_at"], "isoformat") else str(article["published_at"])

        full_text = (
            f"# {title}\n\n"
            f"Source: Economic Times\n"
            f"Category: {category}\n"
            f"Published: {published_at}\n\n"
            f"{content_text}"
        )

        if len(full_text.strip()) < 50:
            continue

        # Create Document record in shared DB
        doc_record = Document(
            title=title,
            source_type=SourceType.news_article,
            source_name="Economic Times",
            original_url=url,
            ingested_at=datetime.utcnow(),
            metadata_={
                "category": category,
                "published_at": published_at,
                "author": article.get("author"),
                "image_url": article.get("image_url"),
                "tags": article.get("tags", []),
                "fetcher": "news-fetcher",
            },
        )
        db.add(doc_record)
        await db.flush()

        # Create LlamaIndex document and index
        doc_id = f"et_news_{doc_record.id}"
        llama_doc = LlamaDocument(
            text=full_text,
            doc_id=doc_id,
            metadata={
                "document_id": doc_record.id,
                "source_name": "Economic Times",
                "source_type": "news_article",
                "category": category,
                "published_at": published_at,
                "url": url,
            },
        )

        nodes = splitter.get_nodes_from_documents([llama_doc])
        engine.add_nodes(nodes)

        doc_record.llamaindex_doc_id = doc_id
        ingested += 1

    await db.commit()

    # Update stats
    _fetch_stats["last_fetch_time"] = datetime.now(timezone.utc).isoformat()
    _fetch_stats["last_fetch_articles"] = ingested
    _fetch_stats["total_fetches"] += 1
    _fetch_stats["total_articles_ingested"] += ingested
    _fetch_stats["errors"] = _fetch_stats["errors"][-20:]

    logger.info(
        f"News fetch complete: fetched={total_fetched}, ingested={ingested}, skipped={skipped}"
    )
    return {"fetched": total_fetched, "ingested": ingested, "skipped_duplicates": skipped}


async def _scheduled_fetch(engine: NewsIndexEngine):
    """Wrapper for the scheduler job — creates its own DB session."""
    logger.info("Scheduled news fetch starting...")
    async with AsyncSessionLocal() as db:
        try:
            result = await run_news_fetch(engine, db)
            logger.info(f"Scheduled fetch result: {result}")
        except Exception as exc:
            logger.error(f"Scheduled news fetch failed: {exc}", exc_info=True)
            _fetch_stats["errors"].append(
                {"time": datetime.now(timezone.utc).isoformat(), "error": str(exc)}
            )


# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle handler."""
    logger.info("Starting news-fetcher service...")

    # Initialize database tables
    await init_db()
    logger.info("Database tables initialized.")

    # Initialize LlamaIndex engine
    index_engine = NewsIndexEngine()
    index_engine.initialize()
    app.state.engine = index_engine
    logger.info("LlamaIndex engine initialized.")

    # Set up APScheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _scheduled_fetch,
        "interval",
        minutes=settings.news_fetch_interval_minutes,
        args=[index_engine],
        id="news_fetch_job",
        name="Periodic ET news fetch",
        replace_existing=True,
    )
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info(
        f"Scheduler started (interval={settings.news_fetch_interval_minutes}min)."
    )

    # Run initial fetch on startup (in background to not block startup)
    asyncio.create_task(_scheduled_fetch(index_engine))
    logger.info("Initial news fetch triggered.")

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info("News-fetcher service stopped.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Market Research - News Fetcher",
    description="Microservice for fetching Economic Times India news articles.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "news-fetcher"}


@app.post("/fetch")
async def manual_fetch(db: AsyncSession = Depends(get_db)):
    """Manually trigger a news fetch cycle."""
    engine: NewsIndexEngine = app.state.engine
    result = await run_news_fetch(engine, db)
    return {"status": "ok", "result": result}


@app.get("/status")
async def fetch_status():
    """Return fetch statistics and scheduler status."""
    scheduler: AsyncIOScheduler = app.state.scheduler
    job = scheduler.get_job("news_fetch_job")
    next_run = job.next_run_time.isoformat() if job and job.next_run_time else None

    return {
        "last_fetch_time": _fetch_stats["last_fetch_time"],
        "last_fetch_articles": _fetch_stats["last_fetch_articles"],
        "total_fetches": _fetch_stats["total_fetches"],
        "total_articles_ingested": _fetch_stats["total_articles_ingested"],
        "next_scheduled_fetch": next_run,
        "fetch_interval_minutes": settings.news_fetch_interval_minutes,
        "recent_errors": _fetch_stats["errors"][-5:],
    }


@app.get("/articles")
async def recent_articles(db: AsyncSession = Depends(get_db)):
    """Return the most recent 50 articles ingested by this service."""
    result = await db.execute(
        select(Document)
        .where(Document.source_type == SourceType.news_article)
        .where(Document.source_name == "Economic Times")
        .order_by(desc(Document.ingested_at))
        .limit(50)
    )
    docs = result.scalars().all()
    return [
        {
            "id": d.id,
            "title": d.title,
            "url": d.original_url,
            "category": (d.metadata_ or {}).get("category", ""),
            "published_at": (d.metadata_ or {}).get("published_at", ""),
            "ingested_at": d.ingested_at.isoformat() if d.ingested_at else None,
        }
        for d in docs
    ]


@app.get("/categories")
async def available_categories():
    """Return the available Economic Times RSS feed categories."""
    from scrapers.economic_times import RSS_FEEDS
    return {
        "configured": [c.strip() for c in settings.news_categories.split(",")],
        "available": list(RSS_FEEDS.keys()),
    }
