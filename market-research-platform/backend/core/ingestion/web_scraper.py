# filepath: market-research-platform/backend/core/ingestion/web_scraper.py
# Async web scraping utilities. Fetches pages with httpx and extracts
# structured content (title, description, body text) using BeautifulSoup.

import asyncio
import logging

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


async def scrape_url(url: str) -> dict:
    """
    Fetch a single URL and extract its main content.

    Returns:
        dict with keys: title, content, description, url
    """
    try:
        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; MarketResearchBot/1.0)"},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract title: prefer <title>, fall back to first <h1>
        title_tag = soup.find("title")
        if title_tag and title_tag.get_text(strip=True):
            title = title_tag.get_text(strip=True)
        else:
            h1_tag = soup.find("h1")
            title = h1_tag.get_text(strip=True) if h1_tag else "Untitled"

        # Extract meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        description = (
            meta_desc["content"].strip()
            if meta_desc and meta_desc.get("content")
            else ""
        )

        # Extract main text content: prefer <article>, then <main>, fall back to <body>
        content_tag = (
            soup.find("article") or soup.find("main") or soup.find("body")
        )
        if content_tag:
            # Remove script and style elements before extracting text
            for tag in content_tag.find_all(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            content = content_tag.get_text(separator="\n", strip=True)
        else:
            content = ""

        return {
            "title": title,
            "content": content,
            "description": description,
            "url": url,
        }

    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP error scraping {url}: {e.response.status_code}")
        return {"title": "", "content": "", "description": "", "url": url, "error": str(e)}
    except httpx.RequestError as e:
        logger.warning(f"Request error scraping {url}: {e}")
        return {"title": "", "content": "", "description": "", "url": url, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error scraping {url}: {e}")
        return {"title": "", "content": "", "description": "", "url": url, "error": str(e)}


async def scrape_urls(urls: list[str]) -> list[dict]:
    """
    Scrape multiple URLs concurrently.

    Returns:
        List of result dicts from scrape_url, one per URL.
    """
    tasks = [scrape_url(url) for url in urls]
    return await asyncio.gather(*tasks)
