"""Anthropic Economic Index page — snapshot text for diffusion analysis."""
import hashlib
import logging
import re
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "DontPanicDiffusionTracker/1.0 (research)"}


def fetch_economic_index(source: dict, fetch_cycle_id: str) -> list[dict]:
    """Fetch the public research page and store a text excerpt (no heavy scraping)."""
    url = source.get("url", "https://www.anthropic.com/research/economic-index-geography")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=45)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        logger.warning(f"Economic index page fetch failed: {e}")
        return []

    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()[:9000]
    ext = hashlib.md5(text.encode()).hexdigest()[:20]
    now = datetime.now(timezone.utc)
    return [
        {
            "external_id": f"anthropic-econidx-{ext}",
            "title": "Anthropic Economic Index (page snapshot)",
            "content": text,
            "url": url[:2000],
            "published_at": now,
        }
    ]
