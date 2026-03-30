"""Web scraping fetchers for ARC-AGI, SWE-bench, and UK AISI."""
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "AGI-Tracker-Bot/1.0 (research; +https://github.com/akash-singh/dont-panic)",
    "Accept": "text/html,application/xhtml+xml,application/json,*/*",
}
REQUEST_DELAY = 2.0  # seconds between requests


def _get(url: str, **kwargs) -> requests.Response:
    """GET with delay and standard headers."""
    time.sleep(REQUEST_DELAY)
    resp = requests.get(url, headers=HEADERS, timeout=30, **kwargs)
    resp.raise_for_status()
    return resp


def _row_hash(*parts: str) -> str:
    key = "|".join(str(p) for p in parts)
    return hashlib.md5(key.encode()).hexdigest()


# ── ARC-AGI Leaderboard ───────────────────────────────────────────────────────

def fetch_arc_agi(source: dict, fetch_cycle_id: str) -> list[dict]:
    """Scrape the ARC-AGI leaderboard page."""
    url = "https://arcprize.org/leaderboard"
    try:
        resp = _get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        raise RuntimeError(f"ARC-AGI scrape failed: {e}") from e

    items = []

    # Look for table rows
    tables = soup.find_all("table")
    if tables:
        for table in tables:
            rows = table.find_all("tr")
            for row in rows[1:21]:  # skip header, max 20
                cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                if len(cells) < 2:
                    continue
                model_name = cells[0]
                score = cells[1] if len(cells) > 1 else "N/A"
                external_id = _row_hash(model_name, score)
                items.append({
                    "external_id": external_id,
                    "title": f"{model_name}: {score}",
                    "content": f"ARC-AGI score: {score}",
                    "url": url,
                    "published_at": None,
                })
    else:
        # Fallback: look for any structured content
        logger.warning("ARC-AGI: no table found, trying generic content extraction")
        text_blocks = soup.find_all(["li", "div", "p"], class_=lambda c: c and "leaderboard" in c.lower())
        for block in text_blocks[:20]:
            text = block.get_text(strip=True)
            if text:
                external_id = _row_hash(text)
                items.append({
                    "external_id": external_id,
                    "title": text[:200],
                    "content": text[:1000],
                    "url": url,
                    "published_at": None,
                })

    logger.info(f"  ARC-AGI: {len(items)} entries")
    return items


# ── SWE-bench ─────────────────────────────────────────────────────────────────

def fetch_swe_bench(source: dict, fetch_cycle_id: str) -> list[dict]:
    """Fetch SWE-bench leaderboard data from GitHub."""
    api_url = "https://api.github.com/repos/SWE-bench/swe-bench.github.io/contents/"
    try:
        time.sleep(1.0)
        resp = requests.get(api_url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        contents = resp.json()
    except Exception as e:
        raise RuntimeError(f"SWE-bench GitHub API failed: {e}") from e

    # Find JSON files that might be leaderboard data
    leaderboard_candidates = [
        f for f in contents
        if f.get("type") == "file" and f.get("name", "").endswith(".json")
        and any(kw in f.get("name", "").lower() for kw in ["result", "leaderboard", "score"])
    ]

    if not leaderboard_candidates:
        # Fall back to looking in a data directory
        data_dirs = [f for f in contents if f.get("type") == "dir" and f.get("name") in ("data", "_data", "results")]
        for d in data_dirs[:1]:
            try:
                resp2 = requests.get(d["url"], headers=HEADERS, timeout=30)
                resp2.raise_for_status()
                sub_contents = resp2.json()
                leaderboard_candidates = [
                    f for f in sub_contents
                    if f.get("type") == "file" and f.get("name", "").endswith(".json")
                ][:3]
            except Exception:
                pass

    items = []
    for candidate in leaderboard_candidates[:2]:
        download_url = candidate.get("download_url")
        if not download_url:
            continue
        try:
            time.sleep(1.0)
            resp = requests.get(download_url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(f"SWE-bench: failed to download {candidate['name']}: {e}")
            continue

        # data might be a list of model results or a dict
        if isinstance(data, list):
            for entry in data[:20]:
                model = entry.get("model") or entry.get("name") or "Unknown"
                resolved = entry.get("resolved") or entry.get("resolve_rate") or entry.get("score") or 0
                external_id = _row_hash(model, str(resolved))
                items.append({
                    "external_id": external_id,
                    "title": model,
                    "content": f"SWE-bench resolve rate: {resolved}",
                    "url": "https://swe-bench.github.io",
                    "published_at": None,
                })
        elif isinstance(data, dict):
            for model, result in list(data.items())[:20]:
                resolved = result.get("resolved", 0) if isinstance(result, dict) else result
                external_id = _row_hash(model, str(resolved))
                items.append({
                    "external_id": external_id,
                    "title": model,
                    "content": f"SWE-bench resolve rate: {resolved}",
                    "url": "https://swe-bench.github.io",
                    "published_at": None,
                })

    logger.info(f"  SWE-bench: {len(items)} entries")
    return items


# ── UK AI Safety Institute ────────────────────────────────────────────────────

def fetch_aisi(source: dict, fetch_cycle_id: str) -> list[dict]:
    """Scrape UK AISI research publications page."""
    url = "https://www.aisi.gov.uk/research"
    try:
        resp = _get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        raise RuntimeError(f"UK AISI scrape failed: {e}") from e

    items = []
    base_url = "https://www.aisi.gov.uk"

    # Look for article/publication links
    link_candidates = soup.find_all("a", href=True)
    seen_urls: set[str] = set()

    for link in link_candidates:
        href = link.get("href", "")
        title = link.get_text(strip=True)

        # Filter for likely publication links
        if not title or len(title) < 10:
            continue
        if not any(kw in href.lower() for kw in ["/research", "/work", "/report", "/publication", "/paper"]):
            continue

        full_url = urljoin(base_url, href)
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        items.append({
            "external_id": full_url,
            "title": title,
            "content": title,
            "url": full_url,
            "published_at": None,
        })

        if len(items) >= 20:
            break

    if not items:
        # Fallback: any substantial link on the page
        for link in link_candidates[:50]:
            href = link.get("href", "")
            title = link.get_text(strip=True)
            if title and len(title) > 15 and href.startswith("/"):
                full_url = urljoin(base_url, href)
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    items.append({
                        "external_id": full_url,
                        "title": title,
                        "content": title,
                        "url": full_url,
                        "published_at": None,
                    })
                    if len(items) >= 10:
                        break

    logger.info(f"  UK AISI: {len(items)} publications")
    return items


# ── Dispatch ──────────────────────────────────────────────────────────────────

def fetch_scrape_source(source: dict, fetch_cycle_id: str) -> list[dict]:
    """Dispatch to the correct scrape fetcher by source name."""
    name = source.get("name", "").lower()
    if "arc" in name:
        return fetch_arc_agi(source, fetch_cycle_id)
    elif "swe" in name:
        return fetch_swe_bench(source, fetch_cycle_id)
    elif "aisi" in name or "safety institute" in name:
        return fetch_aisi(source, fetch_cycle_id)
    else:
        raise ValueError(f"Unknown scrape source: {source.get('name')}")
