# filepath: market-research-platform/backend/api/routes/scraper.py
# REST endpoint for on-demand web scraping. Scrapes provided URLs,
# persists Document records, and indexes content via LlamaIndex.

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from llama_index.core import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter

from api.dependencies import get_session, get_llama_engine
from config import settings
from core.llamaindex_engine import LlamaIndexEngine
from core.ingestion.web_scraper import scrape_urls
from models.document import Document, SourceType

logger = logging.getLogger(__name__)

router = APIRouter()


class ScrapeRequest(BaseModel):
    urls: list[str]


@router.post("/scrape")
async def scrape(
    body: ScrapeRequest,
    db: AsyncSession = Depends(get_session),
    engine: LlamaIndexEngine = Depends(get_llama_engine),
):
    """
    Scrape one or more URLs, create Document records, and index via LlamaIndex.

    Returns:
        {"scraped": int, "failed": int, "results": [...]}
    """
    if not body.urls:
        raise HTTPException(status_code=400, detail="No URLs provided.")

    scraped_pages = await scrape_urls(body.urls)

    scraped_count = 0
    failed_count = 0
    results = []

    for page in scraped_pages:
        url = page["url"]

        # If scraping returned an error or no content, mark as failed
        if page.get("error") or not page.get("content", "").strip():
            failed_count += 1
            results.append({"url": url, "status": "failed", "error": page.get("error", "No content extracted")})
            continue

        title = page["title"] or "Untitled"
        content = page["content"]
        description = page.get("description", "")

        full_text = f"# {title}\n\n{description}\n\n{content}" if description else f"# {title}\n\n{content}"

        # Create Document record in DB (same pattern as news_ingestion.py)
        doc_record = Document(
            title=title,
            source_type=SourceType.web_scrape,
            source_name=url,
            original_url=url,
            ingested_at=datetime.utcnow(),
            metadata_={"description": description},
        )
        db.add(doc_record)
        await db.flush()  # Get the auto-generated ID

        # Convert to LlamaIndex Document and index
        doc_id = f"web_{doc_record.id}"
        llama_doc = LlamaDocument(
            text=full_text,
            doc_id=doc_id,
            metadata={
                "document_id": doc_record.id,
                "source_name": url,
                "source_type": "web_scrape",
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
        scraped_count += 1
        results.append({"url": url, "status": "ok", "title": title, "document_id": doc_record.id})

    await db.commit()

    return {
        "scraped": scraped_count,
        "failed": failed_count,
        "results": results,
    }
