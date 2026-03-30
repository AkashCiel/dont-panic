"""OpenReview SDK fetcher. Gracefully skips if package or credentials unavailable."""
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

VENUES = [
    "ICLR.cc/2025/Conference",
    "NeurIPS.cc/2024/Conference",
    "ICML.cc/2024/Conference",
]
NOTES_PER_VENUE = 20


def fetch_openreview(
    source: dict,
    fetch_cycle_id: str,
    username: str = "",
    password: str = "",
) -> list[dict]:
    """
    Fetch recent paper submissions from OpenReview for major ML venues.
    Returns empty list if openreview-py is not installed or credentials are absent.
    """
    if not username or not password:
        logger.warning("OpenReview credentials not configured (OPENREVIEW_USERNAME/PASSWORD); skipping")
        return []

    try:
        import openreview
    except ImportError:
        logger.warning("openreview-py not installed; skipping OpenReview source. Install with: pip install openreview-py")
        return []

    try:
        client = openreview.api.OpenReviewClient(
            baseurl="https://api2.openreview.net",
            username=username,
            password=password,
        )
    except Exception as e:
        logger.error(f"Failed to authenticate with OpenReview: {e}")
        return []

    items: list[dict] = []

    for venue in VENUES:
        try:
            notes = client.get_all_notes(
                invitation=f"{venue}/-/Submission",
                details="replyCount",
            )
            for note in notes[:NOTES_PER_VENUE]:
                note_id = note.id
                title = ""
                abstract = ""
                try:
                    content = note.content or {}
                    title = (content.get("title") or {}).get("value", "") if isinstance(content.get("title"), dict) else content.get("title", "")
                    abstract = (content.get("abstract") or {}).get("value", "") if isinstance(content.get("abstract"), dict) else content.get("abstract", "")
                except Exception:
                    pass

                published_at = None
                if note.cdate:
                    try:
                        published_at = datetime.fromtimestamp(note.cdate / 1000, tz=timezone.utc)
                    except Exception:
                        pass

                items.append({
                    "external_id": note_id,
                    "title": title or f"OpenReview submission {note_id[:8]}",
                    "content": abstract[:3000] if abstract else "",
                    "url": f"https://openreview.net/forum?id={note_id}",
                    "published_at": published_at,
                })
        except Exception as e:
            logger.warning(f"OpenReview fetch failed for venue {venue}: {e}")
            continue

    logger.info(f"  OpenReview: {len(items)} submissions across {len(VENUES)} venues")
    return items
