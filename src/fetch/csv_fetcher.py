"""CSV download fetcher for Epoch AI datasets."""
import hashlib
import io
import logging
from datetime import datetime, timezone
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Candidate URLs for Epoch AI model data
EPOCH_MODELS_URLS = [
    "https://epoch.ai/data/ai-models.csv",
    "https://epochai.org/data/ai-models.csv",
]

# Candidate URLs for Epoch AI benchmark data
EPOCH_BENCHMARKS_URLS = [
    "https://epoch.ai/data/benchmark-performance.csv",
    "https://epochai.org/data/benchmark-performance.csv",
]

HEADERS = {"User-Agent": "AGI-Tracker-Bot/1.0 (research)"}
MAX_ROWS = 50


def _row_hash(row_values: list) -> str:
    """Generate a stable hash for a CSV row."""
    key = "|".join(str(v) for v in row_values)
    return hashlib.md5(key.encode()).hexdigest()


def _find_column(df_columns: list[str], candidates: list[str]) -> Optional[str]:
    """Find the first matching column name from candidates."""
    cols_lower = {c.lower(): c for c in df_columns}
    for candidate in candidates:
        if candidate.lower() in cols_lower:
            return cols_lower[candidate.lower()]
    return None


def _download_csv(urls: list[str]) -> Optional[bytes]:
    """Try each URL in order, return raw bytes on first success."""
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=60)
            resp.raise_for_status()
            return resp.content
        except Exception as e:
            logger.warning(f"CSV download failed for {url}: {e}")
    return None


def _parse_csv_to_items(csv_bytes: bytes, source: dict, fetch_cycle_id: str) -> list[dict]:
    """Parse CSV bytes into item dicts."""
    try:
        import pandas as pd
    except ImportError:
        raise RuntimeError("pandas is required for CSV fetching: pip install pandas")

    try:
        df = pd.read_csv(io.BytesIO(csv_bytes), encoding="utf-8", low_memory=False)
    except Exception:
        df = pd.read_csv(io.BytesIO(csv_bytes), encoding="latin-1", low_memory=False)

    if df.empty:
        return []

    cols = list(df.columns)
    name_col = _find_column(cols, ["Model", "model", "Name", "name", "System", "system"])
    date_col = _find_column(cols, ["Publication date", "Date", "date", "Release date", "Year"])

    # Limit to most recent rows
    df = df.tail(MAX_ROWS)

    items = []
    for _, row in df.iterrows():
        row_vals = list(row.values)
        external_id = _row_hash(row_vals)

        title = str(row[name_col]) if name_col and name_col in row else f"Row {external_id[:8]}"

        # Build content from all columns as key=value pairs
        content_parts = []
        for col in cols[:20]:  # cap at 20 columns
            val = row.get(col, "")
            if val is not None and str(val) not in ("", "nan", "NaN"):
                content_parts.append(f"{col}: {val}")
        content = "; ".join(content_parts)[:3000]

        # Published date
        published_at = None
        if date_col and date_col in row:
            date_val = str(row[date_col])
            for fmt in ("%Y-%m-%d", "%Y", "%m/%d/%Y", "%d/%m/%Y"):
                try:
                    published_at = datetime.strptime(date_val[:10], fmt).replace(tzinfo=timezone.utc)
                    break
                except ValueError:
                    continue

        items.append({
            "external_id": external_id,
            "title": title[:500],
            "content": content,
            "url": source.get("url", ""),
            "published_at": published_at,
        })

    return items


def fetch_epoch_ai_models(source: dict, fetch_cycle_id: str) -> list[dict]:
    """Download and parse Epoch AI AI models dataset."""
    csv_bytes = _download_csv(EPOCH_MODELS_URLS)
    if csv_bytes is None:
        raise RuntimeError("Failed to download Epoch AI models CSV from all candidate URLs")
    items = _parse_csv_to_items(csv_bytes, source, fetch_cycle_id)
    logger.info(f"  Epoch AI models: {len(items)} rows")
    return items


def fetch_epoch_ai_benchmarks(source: dict, fetch_cycle_id: str) -> list[dict]:
    """Download and parse Epoch AI benchmarks dataset."""
    csv_bytes = _download_csv(EPOCH_BENCHMARKS_URLS)
    if csv_bytes is None:
        raise RuntimeError("Failed to download Epoch AI benchmarks CSV from all candidate URLs")
    items = _parse_csv_to_items(csv_bytes, source, fetch_cycle_id)
    logger.info(f"  Epoch AI benchmarks: {len(items)} rows")
    return items


def fetch_csv_source(source: dict, fetch_cycle_id: str) -> list[dict]:
    """Dispatch to the correct CSV fetcher by source name."""
    name = source.get("name", "").lower()
    if "dataset" in name or "ai model" in name:
        return fetch_epoch_ai_models(source, fetch_cycle_id)
    else:
        return fetch_epoch_ai_benchmarks(source, fetch_cycle_id)
