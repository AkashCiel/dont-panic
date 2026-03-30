"""GraphQL fetcher for LessWrong."""
import logging
import time
from datetime import datetime, timezone
from typing import Optional

import requests

logger = logging.getLogger(__name__)

LESSWRONG_ENDPOINT = "https://www.lesswrong.com/graphql"
MIN_SCORE = 30

LESSWRONG_QUERY = """
{
  posts(input: { terms: { view: "new", limit: 50 } }) {
    results {
      _id
      title
      postedAt
      baseScore
      commentCount
      pageUrl
    }
  }
}
"""


def _parse_iso(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(date_str[:26], fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def fetch_lesswrong(source: dict, fetch_cycle_id: str) -> list[dict]:
    """Fetch LessWrong posts via GraphQL, filtering to baseScore > 30."""
    time.sleep(1.0)

    try:
        resp = requests.post(
            LESSWRONG_ENDPOINT,
            json={"query": LESSWRONG_QUERY},
            headers={"Content-Type": "application/json", "User-Agent": "AGI-Tracker-Bot/1.0"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise RuntimeError(f"LessWrong GraphQL request failed: {e}") from e

    posts = data.get("data", {}).get("posts", {}).get("results", [])
    items = []

    for post in posts:
        base_score = post.get("baseScore", 0) or 0
        if base_score <= MIN_SCORE:
            continue

        post_id = post.get("_id", "")
        page_url = post.get("pageUrl", "") or f"https://www.lesswrong.com/posts/{post_id}"
        comment_count = post.get("commentCount", 0) or 0

        items.append({
            "external_id": post_id,
            "title": post.get("title", ""),
            "content": f"Score: {base_score}, Comments: {comment_count}",
            "url": page_url,
            "published_at": _parse_iso(post.get("postedAt")),
        })

    logger.info(f"  LessWrong: {len(items)} posts with score > {MIN_SCORE} (out of {len(posts)} fetched)")
    return items
