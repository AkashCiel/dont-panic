"""Government procurement / spending APIs (SAM.gov, USAspending, TED EU)."""
import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

logger = logging.getLogger(__name__)

HEADERS_JSON = {
    "User-Agent": "DontPanicDiffusionTracker/1.0 (research)",
    "Accept": "application/json",
}


def _item_from_dict(
    d: dict,
    title_keys: tuple[str, ...],
    content_keys: tuple[str, ...],
    url_keys: tuple[str, ...],
    date_keys: tuple[str, ...],
    base_id: str,
) -> dict:
    title = next((str(d.get(k) or "") for k in title_keys if d.get(k)), "") or json.dumps(d, default=str)[:500]
    content_parts = []
    for k in content_keys:
        v = d.get(k)
        if v:
            content_parts.append(f"{k}: {v}")
    content = "; ".join(content_parts)[:10000] if content_parts else json.dumps(d, default=str)[:8000]
    url = next((str(d.get(k) or "") for k in url_keys if d.get(k)), "")
    published_at = None
    for k in date_keys:
        v = d.get(k)
        if not v:
            continue
        try:
            if isinstance(v, str):
                published_at = datetime.fromisoformat(v.replace("Z", "+00:00"))
            break
        except Exception:
            continue
    h = hashlib.md5(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()[:24]
    return {
        "external_id": f"{base_id}-{h}"[:500],
        "title": title[:2000],
        "content": content,
        "url": url[:2000],
        "published_at": published_at,
    }


def fetch_sam_gov(source: dict, fetch_cycle_id: str, api_key: str) -> list[dict]:
    """SAM.gov contract opportunities (requires SAM_GOV_API_KEY)."""
    if not api_key:
        logger.warning("SAM.gov: SAM_GOV_API_KEY not set — skipping")
        return []

    posted_from = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%m/%d/%Y")
    posted_to = datetime.now(timezone.utc).strftime("%m/%d/%Y")
    params = {
        "api_key": api_key,
        "postedFrom": posted_from,
        "postedTo": posted_to,
        "limit": 50,
        "keywords": "artificial intelligence OR machine learning OR large language model",
    }
    base = source.get("url", "https://api.sam.gov/prod/opportunities/v2/search")
    try:
        resp = requests.get(base, params=params, headers=HEADERS_JSON, timeout=90)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning(f"SAM.gov request failed: {e}")
        return []

    opps = data.get("opportunitiesData") or data.get("data") or []
    if not isinstance(opps, list):
        opps = []

    items: list[dict] = []
    for opp in opps[:50]:
        if not isinstance(opp, dict):
            continue
        items.append(
            _item_from_dict(
                opp,
                title_keys=("title", "opportunityTitle", "subject"),
                content_keys=("description", "agency", "type", "responseDeadLine"),
                url_keys=("uiLink", "resourceLinks", "url"),
                date_keys=("postedDate", "posted_date"),
                base_id="sam",
            )
        )
    logger.info(f"  SAM.gov: {len(items)} items")
    return items


def fetch_usaspending(source: dict, fetch_cycle_id: str) -> list[dict]:
    """USAspending spending-by-award search (keyword + NAICS IT-related)."""
    url = source.get("url", "https://api.usaspending.gov/api/v2/search/spending_by_award/")
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=90)
    payload: dict[str, Any] = {
        "filters": {
            "keywords": ["artificial intelligence"],
            "time_period": [{"start_date": start.isoformat(), "end_date": end.isoformat()}],
        },
        "fields": ["Award ID", "Recipient Name", "Award Amount", "Description", "Awarding Agency", "Start Date", "generated_internal_id"],
        "page": 1,
        "limit": 50,
        "sort": "Award Amount",
        "order": "desc",
    }
    try:
        resp = requests.post(url, json=payload, headers={**HEADERS_JSON, "Content-Type": "application/json"}, timeout=90)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning(f"USAspending request failed: {e}")
        return []

    results = data.get("results") or []
    items: list[dict] = []
    for row in results[:50]:
        if not isinstance(row, dict):
            continue
        items.append(
            _item_from_dict(
                row,
                title_keys=("Description", "Award ID", "Recipient Name"),
                content_keys=("Award Amount", "Awarding Agency", "Start Date"),
                url_keys=(),
                date_keys=("Start Date", "Last Modified Date"),
                base_id="usaspend",
            )
        )
    logger.info(f"  USAspending: {len(items)} items")
    return items


def fetch_ted_eu(source: dict, fetch_cycle_id: str) -> list[dict]:
    """TED Europa public procurement notices (v3 search API)."""
    base = source.get("url", "https://api.ted.europa.eu/v3/notices/search")
    params = {
        "query": "artificial intelligence OR machine learning",
        "limit": 40,
        "scope": "3",
    }
    try:
        resp = requests.get(base, params=params, headers=HEADERS_JSON, timeout=90)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning(f"TED EU request failed: {e}")
        return []

    notices = data.get("notices") or data.get("results") or data.get("data") or []
    if isinstance(data, list):
        notices = data
    if not isinstance(notices, list):
        notices = []

    items: list[dict] = []
    for n in notices[:40]:
        if not isinstance(n, dict):
            continue
        items.append(
            _item_from_dict(
                n,
                title_keys=("title", "noticeTitle", "procedureTitle"),
                content_keys=("description", "buyerName", "estimatedValue", "country"),
                url_keys=("links", "url", "noticeURL"),
                date_keys=("publicationDate", "deadline"),
                base_id="ted",
            )
        )
    logger.info(f"  TED EU: {len(items)} items")
    return items
