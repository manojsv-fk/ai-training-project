# filepath: market-research-platform/backend/core/scheduler/jobs.py
# APScheduler background job definitions.
# Two recurring jobs:
#   1. News sync — pulls fresh articles on a configurable interval
#   2. Weekly brief — generates a scheduled executive summary on a cron schedule

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from config import settings

logger = logging.getLogger(__name__)

# Singleton scheduler instance
scheduler = AsyncIOScheduler()

# Shared app state for tracking last sync time
_app_state = {
    "last_news_sync": None,
    "last_brief_generated": None,
}


def get_app_state() -> dict:
    """Return the current app state dict."""
    return _app_state


def start_scheduler():
    """
    Register all background jobs and start the scheduler.
    Called from main.py lifespan startup hook.
    """
    # Job 1: News sync on a configurable interval
    # Skip if news-fetcher microservice is configured (it handles its own scheduling)
    if settings.news_fetcher_url:
        logger.info(
            f"News fetcher microservice configured at {settings.news_fetcher_url}; "
            "skipping local news_sync scheduler job."
        )
    else:
        scheduler.add_job(
            func=_news_sync_job,
            trigger=IntervalTrigger(minutes=settings.news_sync_interval_minutes),
            id="news_sync",
            replace_existing=True,
            name="News Article Sync",
        )

    # Job 2: Weekly brief generation on a cron schedule
    try:
        scheduler.add_job(
            func=_weekly_brief_job,
            trigger=CronTrigger.from_crontab(settings.weekly_brief_cron),
            id="weekly_brief",
            replace_existing=True,
            name="Weekly Brief Generation",
        )
    except Exception as e:
        logger.warning(f"Failed to schedule weekly brief (invalid cron?): {e}")

    scheduler.start()
    if settings.news_fetcher_url:
        logger.info(
            f"Scheduler started: news sync delegated to {settings.news_fetcher_url}, "
            f"weekly brief cron: {settings.weekly_brief_cron}"
        )
    else:
        logger.info(
            f"Scheduler started: news sync every {settings.news_sync_interval_minutes}min, "
            f"weekly brief cron: {settings.weekly_brief_cron}"
        )


def shutdown_scheduler():
    """Stop the scheduler gracefully. Called from main.py lifespan shutdown hook."""
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down.")


async def _news_sync_job():
    """
    Scheduled news ingestion job.
    Runs on the interval configured in settings.news_sync_interval_minutes.
    """
    logger.info("Running scheduled news sync...")

    try:
        # Import here to avoid circular imports
        from core.llamaindex_engine import get_engine
        from core.ingestion.news_ingestion import run_news_sync
        from database import AsyncSessionLocal

        engine = get_engine()

        async with AsyncSessionLocal() as db:
            result = await run_news_sync(engine, db)
            _app_state["last_news_sync"] = datetime.now(timezone.utc).isoformat()
            logger.info(f"News sync complete: {result}")

    except Exception as e:
        logger.error(f"News sync job failed: {e}")


async def _weekly_brief_job():
    """
    Scheduled weekly brief generation job.
    Runs on the cron schedule configured in settings.weekly_brief_cron.
    """
    logger.info("Running scheduled weekly brief generation...")

    try:
        from core.llamaindex_engine import get_engine
        from core.query.summary_engine import SummaryEngine
        from models.report import Report, ReportType
        from database import AsyncSessionLocal

        engine = get_engine()
        summary_engine = SummaryEngine(engine)

        topics = [t.strip() for t in settings.news_topics.split(",") if t.strip()]
        brief_content = await summary_engine.generate_scheduled_brief(topics)

        # Save as a scheduled report
        async with AsyncSessionLocal() as db:
            report = Report(
                title=f"Weekly Brief - {datetime.now(timezone.utc).strftime('%B %d, %Y')}",
                report_type=ReportType.executive_summary,
                content=brief_content,
                is_scheduled=True,
                schedule_config={"type": "weekly", "topics": topics},
                source_document_ids=[],
            )
            db.add(report)
            await db.commit()

        _app_state["last_brief_generated"] = datetime.now(timezone.utc).isoformat()
        logger.info("Weekly brief generated and saved.")

    except Exception as e:
        logger.error(f"Weekly brief job failed: {e}")
