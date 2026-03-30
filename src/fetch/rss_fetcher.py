"""RSS/Atom feed fetcher using feedparser."""
import logging
import re
import time
from datetime import datetime, timezone
from typing import Optional

import feedparser

logger = logging.getLogger(__name__)

# Sources that need a longer delay (arXiv rate limit policy)
ARXIV_SOURCE_NAMES = {"arxiv cs.ai", "arxiv cs.lg", "arxiv cs.cl"}
ITEMS_PER_FEED = 50


def _strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    try:
        from bs4 import BeautifulSoup
        return BeautifulSoup(text, "html.parser").get_text(separator=" ").strip()
    except ImportError:
        return re.sub(r"<[^>]+>", " ", text).strip()


def _parse_published(entry) -> Optional[datetime]:
    """Parse published_parsed tuple from feedparser entry into a UTC datetime."""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            t = entry.published_parsed
            return datetime(t[0], t[1], t[2], t[3], t[4], t[5], tzinfo=timezone.utc)
        except Exception:
            pass
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        try:
            t = entry.updated_parsed
            return datetime(t[0], t[1], t[2], t[3], t[4], t[5], tzinfo=timezone.utc)
        except Exception:
            pass
    return None


def fetch_rss(source: dict, fetch_cycle_id: str) -> list[dict]:
    """
    Fetch an RSS/Atom feed and return a list of item dicts.
    Each item: {external_id, title, content, url, published_at}
    """
    url = source.get("url", "")
    source_name = source.get("name", "")
    is_arxiv = source_name.lower() in ARXIV_SOURCE_NAMES

    delay = 3.0 if is_arxiv else 1.0

    logger.info(f"Fetching RSS: {source_name} ({url})")
    time.sleep(delay)

    try:
        feed = feedparser.parse(url)
    except Exception as e:
        raise RuntimeError(f"feedparser failed for {url}: {e}") from e

    if feed.bozo and not feed.entries:
        raise RuntimeError(f"Feed parse error for {url}: {feed.bozo_exception}")

    items = []
    for entry in feed.entries[:ITEMS_PER_FEED]:
        # external_id: prefer guid, fall back to link
        external_id = getattr(entry, "id", None) or getattr(entry, "link", None)
        if not external_id:
            continue

        title = getattr(entry, "title", "") or ""
        link = getattr(entry, "link", "") or ""

        # Content: prefer content[0].value, then summary, then description
        content_raw = ""
        if hasattr(entry, "content") and entry.content:
            content_raw = entry.content[0].get("value", "")
        elif hasattr(entry, "summary"):
            content_raw = entry.summary or ""
        elif hasattr(entry, "description"):
            content_raw = entry.description or ""

        content = _strip_html(content_raw)[:4000]  # truncate for DB

        items.append({
            "external_id": external_id,
            "title": _strip_html(title),
            "content": content,
            "url": link,
            "published_at": _parse_published(entry),
        })

    logger.info(f"  {source_name}: parsed {len(items)} entries")
    return items
