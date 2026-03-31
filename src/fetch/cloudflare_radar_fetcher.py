"""Cloudflare Radar AI time-series (bots + inference)."""
import hashlib
import json
import logging
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

HEADERS_BASE = {
    "User-Agent": "DontPanicDiffusionTracker/1.0 (research)",
    "Accept": "application/json",
}


def fetch_cloudflare_radar(source: dict, fetch_cycle_id: str, api_token: str) -> list[dict]:
    """
    Fetch Radar AI endpoints; store JSON summaries as one or two items per cycle.
    Requires CLOUDFLARE_API_TOKEN with Radar read.
    """
    if not api_token:
        logger.warning("Cloudflare Radar: CLOUDFLARE_API_TOKEN not set — skipping")
        return []

    headers = {**HEADERS_BASE, "Authorization": f"Bearer {api_token}"}
    endpoints = [
        "https://api.cloudflare.com/client/v4/radar/ai/bots/timeseries",
        "https://api.cloudflare.com/client/v4/radar/ai/inference/timeseries",
    ]
    parts: list[str] = []
    for ep in endpoints:
        try:
            resp = requests.get(ep, headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            parts.append(f"=== {ep.split('/')[-1]} ===\n{json.dumps(data, default=str)[:12000]}")
        except Exception as e:
            logger.warning(f"Cloudflare Radar {ep} failed: {e}")

    if not parts:
        return []

    blob = "\n\n".join(parts)
    ext = hashlib.md5(blob.encode()).hexdigest()[:24]
    now = datetime.now(timezone.utc)
    return [
        {
            "external_id": f"cf-radar-{ext}",
            "title": "Cloudflare Radar AI metrics snapshot",
            "content": blob[:10000],
            "url": source.get("url", "https://radar.cloudflare.com/")[:2000],
            "published_at": now,
        }
    ]
