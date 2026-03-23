# filepath: market-research-platform/news-fetcher/scrapers/economic_times.py
# Economic Times India scraper. Combines RSS feed parsing with async web
# scraping to fetch full article content from economictimes.indiatimes.com.

import asyncio
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# RSS feed URLs by category
RSS_FEEDS: dict[str, str] = {
    "markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "industry": "https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms",
    "tech": "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",
    "economy": "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms",
    "politics": "https://economictimes.indiatimes.com/news/politics-and-nation/rssfeeds/1052732854.cms",
    "companies": "https://economictimes.indiatimes.com/markets/companies/rssfeeds/2143429.cms",
    "startups": "https://economictimes.indiatimes.com/tech/startups/rssfeeds/78570550.cms",
}

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Delay between individual article scrape requests (seconds)
REQUEST_DELAY_MIN = 0.5
REQUEST_DELAY_MAX = 1.0


class EconomicTimesScraper:
    """Scraper for Economic Times India articles via RSS feeds and web scraping."""

    def __init__(
        self,
        categories: list[str] | None = None,
        timeout: float = 15.0,
    ) -> None:
        """
        Args:
            categories: List of RSS category keys to fetch. If ``None``, all
                available categories are used.  Valid keys:
                markets, industry, tech, economy, politics, companies, startups.
            timeout: HTTP request timeout in seconds.
        """
        if categories:
            unknown = set(categories) - set(RSS_FEEDS)
            if unknown:
                logger.warning(
                    "Unknown categories ignored: %s. Valid: %s",
                    unknown,
                    list(RSS_FEEDS.keys()),
                )
            self._feeds = {
                k: v for k, v in RSS_FEEDS.items() if k in categories
            }
        else:
            self._feeds = dict(RSS_FEEDS)

        self._timeout = timeout

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def fetch_articles(
        self, max_per_category: int = 15
    ) -> list[dict]:
        """Fetch articles from all configured RSS categories.

        For each article the scraper first collects metadata from the RSS feed,
        then attempts to scrape the full article text from the webpage.  If the
        full-content scrape fails the RSS summary is used as fallback.

        Args:
            max_per_category: Maximum number of articles to return per RSS
                category.

        Returns:
            List of article dicts (see module docstring for schema).
        """
        tasks = [
            self._fetch_rss_feed(category, url, max_per_category)
            for category, url in self._feeds.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        articles: list[dict] = []
        for result in results:
            if isinstance(result, BaseException):
                logger.error("RSS feed task failed: %s", result)
                continue
            articles.extend(result)

        logger.info(
            "EconomicTimesScraper: fetched %d articles across %d categories",
            len(articles),
            len(self._feeds),
        )
        return articles

    # ------------------------------------------------------------------
    # RSS feed parsing
    # ------------------------------------------------------------------

    async def _fetch_rss_feed(
        self, category: str, url: str, max_articles: int
    ) -> list[dict]:
        """Fetch and parse a single RSS feed, then scrape full content.

        Args:
            category: Human-readable category name (e.g. "markets").
            url: RSS feed URL.
            max_articles: Cap on the number of entries to process.

        Returns:
            List of article dicts.
        """
        try:
            feed = await asyncio.to_thread(feedparser.parse, url)
        except Exception as exc:
            logger.warning(
                "Failed to parse RSS feed for %s: %s", category, exc
            )
            return []

        entries = feed.entries[:max_articles]
        if not entries:
            logger.debug("No entries in RSS feed for category '%s'", category)
            return []

        logger.info(
            "RSS [%s]: processing %d entries", category, len(entries)
        )

        articles: list[dict] = []

        async with httpx.AsyncClient(
            timeout=self._timeout,
            follow_redirects=True,
            headers=DEFAULT_HEADERS,
        ) as client:
            for entry in entries:
                article = self._parse_rss_entry(entry, category)
                if not article["url"]:
                    continue

                # Attempt full-content scrape
                scraped = await self._scrape_article_content(
                    article["url"], client
                )
                if scraped.get("content"):
                    article["content"] = scraped["content"]
                if scraped.get("author"):
                    article["author"] = scraped["author"]
                if scraped.get("image_url"):
                    article["image_url"] = scraped["image_url"]
                if scraped.get("tags"):
                    article["tags"] = scraped["tags"]
                if scraped.get("published_at") and article["published_at"] is None:
                    article["published_at"] = scraped["published_at"]

                articles.append(article)

                # Rate-limit between requests
                await asyncio.sleep(
                    REQUEST_DELAY_MIN
                    + (REQUEST_DELAY_MAX - REQUEST_DELAY_MIN) * 0.5
                )

        return articles

    @staticmethod
    def _parse_rss_entry(entry, category: str) -> dict:
        """Convert a single feedparser entry into the article dict schema."""
        summary_raw = entry.get("summary", "") or ""
        # Strip HTML tags from RSS summary
        summary = BeautifulSoup(summary_raw, "html.parser").get_text(
            separator=" ", strip=True
        )

        published_at = None
        published_str = entry.get("published") or entry.get("updated")
        if published_str:
            try:
                published_at = parsedate_to_datetime(published_str)
                if published_at.tzinfo is None:
                    published_at = published_at.replace(tzinfo=timezone.utc)
            except Exception:
                # Fallback: try ISO format
                try:
                    published_at = datetime.fromisoformat(
                        published_str.replace("Z", "+00:00")
                    )
                except Exception:
                    pass

        return {
            "title": entry.get("title", "").strip(),
            "url": entry.get("link", "").strip(),
            "summary": summary,
            "content": summary,  # fallback; overwritten if scrape succeeds
            "author": None,
            "published_at": published_at,
            "category": category,
            "source": "economic_times",
            "image_url": None,
            "tags": [],
        }

    # ------------------------------------------------------------------
    # Full article scraping
    # ------------------------------------------------------------------

    async def _scrape_article_content(
        self, url: str, client: httpx.AsyncClient
    ) -> dict:
        """Scrape full article content from an ET article page.

        Args:
            url: Article URL.
            client: Reusable ``httpx.AsyncClient`` for connection pooling.

        Returns:
            Dict with optional keys: content, author, image_url, tags,
            published_at.  Missing keys indicate the value could not be
            extracted.
        """
        result: dict = {}
        try:
            response = await client.get(url)
            response.raise_for_status()

            # Handle potential encoding issues
            html = response.text
            soup = BeautifulSoup(html, "html.parser")

            # -- Article text --
            article_text = await self._extract_article_text(soup)
            if article_text:
                result["content"] = article_text

            # -- Author --
            author = self._extract_author(soup)
            if author:
                result["author"] = author

            # -- Image --
            image_url = self._extract_image(soup)
            if image_url:
                result["image_url"] = image_url

            # -- Tags / keywords --
            tags = self._extract_tags(soup)
            if tags:
                result["tags"] = tags

            # -- Published date from meta --
            pub_date = self._extract_published_date(soup)
            if pub_date:
                result["published_at"] = pub_date

        except httpx.HTTPStatusError as exc:
            logger.warning(
                "HTTP %d scraping article %s", exc.response.status_code, url
            )
        except httpx.RequestError as exc:
            logger.warning("Request error scraping %s: %s", url, exc)
        except Exception as exc:
            logger.error("Unexpected error scraping %s: %s", url, exc)

        return result

    async def _extract_article_text(self, soup: BeautifulSoup) -> str:
        """Extract main article text from parsed HTML.

        Tries multiple selectors that Economic Times uses for article bodies.
        """
        # Ordered list of selectors to try (most specific first)
        selectors = [
            {"class_": "artText"},
            {"class_": "Normal"},
            {"class_": "article_content"},
            {"class_": "story_content"},
            {"class_": "main-content"},
        ]

        content_div = None
        for sel in selectors:
            content_div = soup.find("div", **sel)
            if content_div:
                break

        # Fallback: look for <article> tag
        if not content_div:
            content_div = soup.find("article")

        if not content_div:
            return ""

        # Remove unwanted elements
        for tag in content_div.find_all(
            ["script", "style", "nav", "footer", "header", "aside", "iframe"]
        ):
            tag.decompose()

        # Also remove ad-related divs and social share widgets
        for tag in content_div.find_all(
            "div",
            class_=lambda c: c and any(
                kw in (c if isinstance(c, str) else " ".join(c))
                for kw in ("adContainer", "ad-slot", "social", "share", "related")
            ),
        ):
            tag.decompose()

        paragraphs = content_div.find_all("p")
        if paragraphs:
            text = "\n\n".join(
                p.get_text(separator=" ", strip=True)
                for p in paragraphs
                if p.get_text(strip=True)
            )
        else:
            text = content_div.get_text(separator="\n", strip=True)

        return text.strip()

    # ------------------------------------------------------------------
    # Metadata extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_author(soup: BeautifulSoup) -> str | None:
        """Extract author name from the article page."""
        # Try meta tag first
        meta_author = soup.find("meta", attrs={"name": "author"})
        if meta_author and meta_author.get("content", "").strip():
            return meta_author["content"].strip()

        # Try common ET author selectors
        for selector in [
            {"class_": "artByline"},
            {"class_": "author"},
            {"class_": "byline"},
            {"class_": "artAuth"},
        ]:
            tag = soup.find(["span", "div", "a"], **selector)
            if tag:
                name = tag.get_text(strip=True)
                if name:
                    return name

        return None

    @staticmethod
    def _extract_image(soup: BeautifulSoup) -> str | None:
        """Extract the primary article image URL."""
        # og:image meta tag (most reliable)
        og_img = soup.find("meta", attrs={"property": "og:image"})
        if og_img and og_img.get("content", "").strip():
            return og_img["content"].strip()

        # Fallback: first image inside the article body
        for sel in [{"class_": "artText"}, {"class_": "article_content"}]:
            container = soup.find("div", **sel)
            if container:
                img = container.find("img", src=True)
                if img:
                    return img["src"]

        return None

    @staticmethod
    def _extract_tags(soup: BeautifulSoup) -> list[str]:
        """Extract article tags/keywords."""
        # Try meta keywords
        meta_kw = soup.find("meta", attrs={"name": "keywords"})
        if meta_kw and meta_kw.get("content", "").strip():
            return [
                t.strip()
                for t in meta_kw["content"].split(",")
                if t.strip()
            ]

        # Try article:tag meta tags
        tag_metas = soup.find_all("meta", attrs={"property": "article:tag"})
        if tag_metas:
            return [
                m["content"].strip()
                for m in tag_metas
                if m.get("content", "").strip()
            ]

        return []

    @staticmethod
    def _extract_published_date(soup: BeautifulSoup) -> datetime | None:
        """Extract published date from meta tags."""
        for attr in [
            {"property": "article:published_time"},
            {"name": "publish-date"},
            {"property": "og:updated_time"},
        ]:
            meta = soup.find("meta", attrs=attr)
            if meta and meta.get("content", "").strip():
                try:
                    dt = datetime.fromisoformat(
                        meta["content"].strip().replace("Z", "+00:00")
                    )
                    return dt
                except (ValueError, TypeError):
                    continue
        return None
