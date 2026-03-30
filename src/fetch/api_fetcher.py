"""REST API fetchers: Semantic Scholar, DeepSeek (GitHub + HuggingFace), HuggingFace leaderboard."""
import logging
import time
from datetime import datetime, timezone
from typing import Optional

import requests

logger = logging.getLogger(__name__)

SEMANTIC_SCHOLAR_ENDPOINT = "https://api.semanticscholar.org/graph/v1/paper/search"
SEMANTIC_SCHOLAR_QUERIES = [
    "AI reasoning",
    "world models artificial intelligence",
    "causal reasoning neural networks",
    "self-directed learning AI",
]
SEMANTIC_SCHOLAR_FIELDS = "paperId,title,abstract,url,year,publicationDate"

GITHUB_API_BASE = "https://api.github.com"
HF_API_BASE = "https://huggingface.co/api"


def _parse_iso_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO 8601 date string to UTC datetime."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _default_headers(github_token: str = "") -> dict:
    headers = {"User-Agent": "AGI-Tracker-Bot/1.0"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    return headers


# ── Semantic Scholar ──────────────────────────────────────────────────────────

def fetch_semantic_scholar(source: dict, fetch_cycle_id: str, api_key: str = "") -> list[dict]:
    """Search Semantic Scholar for AI research papers across multiple queries."""
    headers = {"User-Agent": "AGI-Tracker-Bot/1.0"}
    if api_key:
        headers["x-api-key"] = api_key

    seen_ids: set[str] = set()
    items: list[dict] = []

    for query in SEMANTIC_SCHOLAR_QUERIES:
        time.sleep(1.1)  # 1 RPS limit
        try:
            resp = requests.get(
                SEMANTIC_SCHOLAR_ENDPOINT,
                params={"query": query, "fields": SEMANTIC_SCHOLAR_FIELDS, "limit": 25},
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.HTTPError as e:
            logger.warning(f"Semantic Scholar query '{query}' failed: {e}")
            continue
        except Exception as e:
            logger.warning(f"Semantic Scholar request error for '{query}': {e}")
            continue

        for paper in data.get("data", []):
            paper_id = paper.get("paperId")
            if not paper_id or paper_id in seen_ids:
                continue
            seen_ids.add(paper_id)

            published_at = _parse_iso_date(paper.get("publicationDate"))

            items.append({
                "external_id": paper_id,
                "title": paper.get("title", ""),
                "content": paper.get("abstract", "") or "",
                "url": paper.get("url", f"https://www.semanticscholar.org/paper/{paper_id}"),
                "published_at": published_at,
            })

    logger.info(f"  Semantic Scholar: {len(items)} papers across {len(SEMANTIC_SCHOLAR_QUERIES)} queries")
    return items


# ── DeepSeek (GitHub + HuggingFace) ──────────────────────────────────────────

def fetch_deepseek(source: dict, fetch_cycle_id: str, github_token: str = "") -> list[dict]:
    """Fetch DeepSeek releases from GitHub repos and HuggingFace models."""
    items: list[dict] = []
    headers = _default_headers(github_token)

    # GitHub repos
    try:
        resp = requests.get(
            f"{GITHUB_API_BASE}/orgs/deepseek-ai/repos",
            params={"sort": "updated", "per_page": 20},
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        for repo in resp.json():
            items.append({
                "external_id": f"github-{repo['id']}",
                "title": repo.get("name", ""),
                "content": repo.get("description", "") or f"Stars: {repo.get('stargazers_count', 0)}",
                "url": repo.get("html_url", ""),
                "published_at": _parse_iso_date(repo.get("updated_at")),
            })
    except Exception as e:
        logger.warning(f"DeepSeek GitHub fetch failed: {e}")

    time.sleep(1.0)

    # HuggingFace models
    try:
        resp = requests.get(
            f"{HF_API_BASE}/models",
            params={"author": "deepseek-ai", "sort": "lastModified", "limit": 15},
            timeout=30,
        )
        resp.raise_for_status()
        for model in resp.json():
            model_id = model.get("modelId") or model.get("id", "")
            tags = ", ".join(model.get("tags", [])[:5])
            items.append({
                "external_id": f"hf-{model_id}",
                "title": model_id,
                "content": tags or f"HuggingFace model: {model_id}",
                "url": f"https://huggingface.co/{model_id}",
                "published_at": _parse_iso_date(model.get("lastModified")),
            })
    except Exception as e:
        logger.warning(f"DeepSeek HuggingFace fetch failed: {e}")

    logger.info(f"  DeepSeek: {len(items)} items")
    return items


# ── HuggingFace Open LLM Leaderboard ─────────────────────────────────────────

def fetch_huggingface_leaderboard(source: dict, fetch_cycle_id: str) -> list[dict]:
    """Fetch top text-generation models from HuggingFace as leaderboard proxy."""
    items: list[dict] = []
    try:
        resp = requests.get(
            f"{HF_API_BASE}/models",
            params={"sort": "downloads", "limit": 30, "filter": "text-generation"},
            timeout=30,
        )
        resp.raise_for_status()
        for model in resp.json():
            model_id = model.get("modelId") or model.get("id", "")
            downloads = model.get("downloads", 0)
            likes = model.get("likes", 0)
            items.append({
                "external_id": model_id,
                "title": model_id,
                "content": f"Model: {model_id}, downloads: {downloads}, likes: {likes}",
                "url": f"https://huggingface.co/{model_id}",
                "published_at": _parse_iso_date(model.get("lastModified")),
            })
    except Exception as e:
        raise RuntimeError(f"HuggingFace leaderboard fetch failed: {e}") from e

    logger.info(f"  HuggingFace leaderboard: {len(items)} models")
    return items


# ── Dispatch ──────────────────────────────────────────────────────────────────

def fetch_api_source(source: dict, fetch_cycle_id: str, config) -> list[dict]:
    """Dispatch to the correct API fetcher based on source name."""
    name = source.get("name", "").lower()
    if "semantic scholar" in name:
        return fetch_semantic_scholar(source, fetch_cycle_id, config.semantic_scholar_api_key)
    elif "deepseek" in name:
        return fetch_deepseek(source, fetch_cycle_id, config.github_token)
    elif "huggingface" in name:
        return fetch_huggingface_leaderboard(source, fetch_cycle_id)
    else:
        raise ValueError(f"Unknown API source: {source.get('name')}")
