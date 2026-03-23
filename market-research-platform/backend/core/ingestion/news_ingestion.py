# filepath: market-research-platform/backend/core/ingestion/news_ingestion.py
# News article ingestion pipeline. Pulls articles from NewsAPI and Google News RSS,
# converts them to LlamaIndex Documents, and indexes them into PGVectorStore.

import logging
from datetime import datetime, timezone
from urllib.parse import quote_plus

import feedparser
from llama_index.core import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from core.llamaindex_engine import LlamaIndexEngine
from models.document import Document, SourceType

logger = logging.getLogger(__name__)


async def run_news_sync(engine: LlamaIndexEngine, db: AsyncSession) -> dict:
    """
    Fetch and ingest news articles from all configured sources.

    Returns:
        dict: { "fetched": int, "ingested": int, "skipped_duplicates": int }
    """
    topics = [t.strip() for t in settings.news_topics.split(",") if t.strip()]
    total_fetched = 0
    ingested = 0
    skipped = 0

    for topic in topics:
        # Fetch from both NewsAPI and Google News RSS
        articles = await _fetch_from_newsapi(topic)
        rss_articles = _fetch_from_google_news_rss(topic)
        articles.extend(rss_articles)
        total_fetched += len(articles)

        for article in articles:
            url = article.get("url", "")
            if not url:
                continue

            # Check for duplicate by original_url
            result = await db.execute(
                select(Document).where(Document.original_url == url)
            )
            if result.scalar_one_or_none():
                skipped += 1
                continue

            # Build article text content
            title = article.get("title", "Untitled")
            description = article.get("description", "")
            content_text = article.get("content", description)
            source_name = article.get("source", {}).get("name", "Unknown")
            published = article.get("publishedAt", datetime.now(timezone.utc).isoformat())

            full_text = f"# {title}\n\nSource: {source_name}\nPublished: {published}\n\n{content_text}"

            if not full_text.strip() or len(full_text) < 50:
                continue

            # Create Document record in DB
            doc_record = Document(
                title=title,
                source_type=SourceType.news_article,
                source_name=source_name,
                original_url=url,
                ingested_at=datetime.now(timezone.utc),
                metadata_={"topic": topic, "published_at": published},
            )
            db.add(doc_record)
            await db.flush()  # Get the auto-generated ID

            # Convert to LlamaIndex Document and index
            doc_id = f"news_{doc_record.id}"
            llama_doc = LlamaDocument(
                text=full_text,
                doc_id=doc_id,
                metadata={
                    "document_id": doc_record.id,
                    "source_name": source_name,
                    "source_type": "news_article",
                    "topic": topic,
                    "published_at": published,
                    "url": url,
                },
            )

            # Chunk and index
            splitter = SentenceSplitter(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            )
            nodes = splitter.get_nodes_from_documents([llama_doc])
            engine.add_nodes(nodes)

            # Update the Document record with the LlamaIndex doc ID
            doc_record.llamaindex_doc_id = doc_id
            ingested += 1

    await db.commit()
    logger.info(
        f"News sync complete: fetched={total_fetched}, ingested={ingested}, skipped={skipped}"
    )
    return {"fetched": total_fetched, "ingested": ingested, "skipped_duplicates": skipped}


async def _fetch_from_newsapi(topic: str) -> list[dict]:
    """
    Fetch articles from NewsAPI for a given topic keyword.
    Returns list of article dicts matching the NewsAPI response schema.
    """
    if not settings.newsapi_key:
        logger.debug("NewsAPI key not configured, skipping NewsAPI fetch")
        return []

    try:
        from newsapi import NewsApiClient

        client = NewsApiClient(api_key=settings.newsapi_key)
        response = client.get_everything(
            q=topic,
            language="en",
            sort_by="publishedAt",
            page_size=10,  # Conservative for POC
        )
        articles = response.get("articles", [])
        logger.info(f"NewsAPI: fetched {len(articles)} articles for topic '{topic}'")
        return articles
    except Exception as e:
        logger.warning(f"NewsAPI fetch failed for topic '{topic}': {e}")
        return []


def _fetch_from_google_news_rss(topic: str) -> list[dict]:
    """
    Fetch articles from Google News RSS for a given topic.
    No API key required. Returns dicts in the same format as NewsAPI articles.
    """
    try:
        encoded_topic = quote_plus(topic)
        url = f"https://news.google.com/rss/search?q={encoded_topic}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)

        articles = []
        for entry in feed.entries[:10]:  # Limit to 10 per topic
            articles.append({
                "title": entry.get("title", ""),
                "description": entry.get("summary", ""),
                "content": entry.get("summary", ""),
                "url": entry.get("link", ""),
                "publishedAt": entry.get("published", ""),
                "source": {"name": entry.get("source", {}).get("title", "Google News")},
            })

        logger.info(f"Google News RSS: fetched {len(articles)} articles for topic '{topic}'")
        return articles
    except Exception as e:
        logger.warning(f"Google News RSS fetch failed for topic '{topic}': {e}")
        return []
