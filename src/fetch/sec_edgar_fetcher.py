"""SEC EDGAR EFTS full-text search — AI-related filings (snippets only)."""
import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

logger = logging.getLogger(__name__)

# SEC requires a descriptive User-Agent with contact info
HEADERS = {
    "User-Agent": "DontPanicDiffusionTracker/1.0 (https://github.com; research)",
    "Accept": "application/json",
}


def _extract_hits(payload: Any) -> list[dict]:
    """Best-effort extraction of hit list from EFTS JSON (schema may vary)."""
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("hits", "results", "items", "data"):
        v = payload.get(key)
        if isinstance(v, list):
            return [x for x in v if isinstance(x, dict)]
        if isinstance(v, dict) and "hits" in v:
            inner = v.get("hits")
            if isinstance(inner, list):
                return [x for x in inner if isinstance(x, dict)]
    return []


def _hit_to_item(hit: dict, source_url: str, fetch_cycle_id: str) -> dict | None:
    """Map one EFTS hit to fetched_items shape."""
    accession = (
        hit.get("adsh")
        or hit.get("accessionNo")
        or hit.get("accession_number")
        or hit.get("fileNumber")
        or hit.get("id")
    )
    title = (
        hit.get("displayNames", [None])[0]
        if isinstance(hit.get("displayNames"), list)
        else None
    ) or hit.get("companyName") or hit.get("company") or hit.get("title") or "SEC filing"
    snippet = hit.get("snippet") or hit.get("summary") or json.dumps(hit, default=str)[:2000]
    url = hit.get("url") or hit.get("link") or source_url
    filed = hit.get("filedAt") or hit.get("filed_at") or hit.get("period")
    published_at = None
    if filed:
        try:
            if isinstance(filed, str):
                published_at = datetime.fromisoformat(filed.replace("Z", "+00:00"))
            elif isinstance(filed, (int, float)):
                published_at = datetime.fromtimestamp(filed, tz=timezone.utc)
        except Exception:
            pass

    if not accession:
        accession = hashlib.md5(json.dumps(hit, sort_keys=True, default=str).encode()).hexdigest()[:32]

    ext = f"sec-{accession}"
    return {
        "external_id": ext[:500],
        "title": str(title)[:2000],
        "content": str(snippet)[:10000],
        "url": str(url)[:2000],
        "published_at": published_at,
    }


def fetch_sec_edgar(source: dict, fetch_cycle_id: str) -> list[dict]:
    """Query EFTS for recent AI-related filings; store snippets only."""
    url_template = source.get("url") or ""
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=14)
    try:
        url = url_template.format(start=start.isoformat(), end=end.isoformat())
    except KeyError:
        url = url_template

    logger.info(f"SEC EDGAR EFTS: {url[:120]}...")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as e:
        logger.warning(f"SEC EFTS request failed: {e}")
        return []

    hits = _extract_hits(payload)
    items: list[dict] = []
    seen: set[str] = set()
    for hit in hits[:80]:
        item = _hit_to_item(hit, source.get("url", ""), fetch_cycle_id)
        if not item:
            continue
        if item["external_id"] in seen:
            continue
        seen.add(item["external_id"])
        items.append(item)

    logger.info(f"  SEC EDGAR: {len(items)} items (from {len(hits)} raw hits)")
    return items
