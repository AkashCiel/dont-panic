"""Database operations — insert, query, and helper functions."""
import json
import logging
from datetime import datetime
from typing import Any, Optional

from src.db.connection import execute_query, execute_non_query, execute_returning, execute_many
from src.db.diffusion_constants import SHARED_DIFFUSION_SOURCE_IDS

logger = logging.getLogger(__name__)


# ── Fetched Items ─────────────────────────────────────────────────────────────

def insert_fetched_item(
    source_id: int,
    external_id: str,
    title: str,
    content: str,
    url: str,
    published_at: Optional[datetime],
    fetch_cycle_id: str,
) -> Optional[int]:
    """
    Insert a fetched item. Ignores duplicates (ON CONFLICT DO NOTHING).
    Returns the new item id, or None if it was a duplicate.
    """
    sql = """
        INSERT INTO fetched_items
            (source_id, external_id, title, content, url, published_at, fetch_cycle_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (source_id, external_id) DO NOTHING
        RETURNING id
    """
    return execute_returning(sql, (source_id, external_id, title, content, url, published_at, fetch_cycle_id))


def get_unprocessed_items(limit: int = 1000) -> list[dict]:
    """Return unprocessed fetched_items for the cognitive track only (excludes diffusion-only sources)."""
    sql = """
        SELECT fi.id, fi.source_id, fi.external_id, fi.title, fi.content,
               fi.url, fi.published_at, fi.fetch_cycle_id,
               s.name as source_name, s.category, s.weight_default
        FROM fetched_items fi
        JOIN sources s ON s.id = fi.source_id
        WHERE fi.processed = false
          AND s.track = 'cognitive'
        ORDER BY fi.fetched_at ASC
        LIMIT %s
    """
    return execute_query(sql, (limit,))


def get_unprocessed_diffusion_items(limit: int = 2000) -> list[dict]:
    """Items not yet analysed by the diffusion pipeline (diffusion-only + shared sources)."""
    sql = """
        SELECT fi.id, fi.source_id, fi.external_id, fi.title, fi.content,
               fi.url, fi.published_at, fi.fetch_cycle_id,
               s.name as source_name, s.category, s.weight_default
        FROM fetched_items fi
        JOIN sources s ON s.id = fi.source_id
        WHERE fi.diffusion_processed = false
          AND (s.track = 'diffusion' OR s.id = ANY(%s))
        ORDER BY fi.fetched_at ASC
        LIMIT %s
    """
    return execute_query(sql, (list(SHARED_DIFFUSION_SOURCE_IDS), limit))


def mark_items_processed(item_ids: list[int]) -> None:
    """Set processed=true for the given item ids."""
    if not item_ids:
        return
    # Use ANY with a list converted to tuple
    sql = "UPDATE fetched_items SET processed = true WHERE id = ANY(%s)"
    execute_non_query(sql, (item_ids,))


def mark_items_diffusion_processed(item_ids: list[int]) -> None:
    """Set diffusion_processed=true for the given item ids."""
    if not item_ids:
        return
    sql = "UPDATE fetched_items SET diffusion_processed = true WHERE id = ANY(%s)"
    execute_non_query(sql, (item_ids,))


# ── Wave 1 Outputs ────────────────────────────────────────────────────────────

def insert_wave1_output(
    report_cycle_id: str,
    fetched_item_id: int,
    source_weight: int,
    weight_justification: str,
    claims: list[dict],
    model_used: str,
    tokens_used: int,
    cost_usd: float,
    track: str = "cognitive",
) -> int:
    """Insert a wave1 output record. Returns its id."""
    sql = """
        INSERT INTO wave1_outputs
            (report_cycle_id, fetched_item_id, source_weight, weight_justification,
             claims, model_used, tokens_used, cost_usd, track)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """
    return execute_returning(
        sql,
        (
            report_cycle_id,
            fetched_item_id,
            source_weight,
            weight_justification,
            json.dumps(claims),
            model_used,
            tokens_used,
            cost_usd,
            track,
        ),
    )


def get_wave1_outputs_for_cycle(report_cycle_id: str) -> list[dict]:
    """Return all wave1 outputs for a report cycle."""
    sql = """
        SELECT w.id, w.report_cycle_id, w.fetched_item_id, w.source_weight,
               w.weight_justification, w.claims, w.model_used, w.tokens_used,
               w.cost_usd, w.created_at,
               fi.source_id, fi.title, fi.url, fi.published_at,
               s.name as source_name, s.category
        FROM wave1_outputs w
        JOIN fetched_items fi ON fi.id = w.fetched_item_id
        JOIN sources s ON s.id = fi.source_id
        WHERE w.report_cycle_id = %s AND w.track = 'cognitive'
        ORDER BY w.id ASC
    """
    rows = execute_query(sql, (report_cycle_id,))
    # claims is stored as JSONB — psycopg2 returns it as a Python object already
    return rows


# ── Reports ───────────────────────────────────────────────────────────────────

def insert_report(
    report_cycle_id: str,
    report_tree: dict,
    scenario_assessment: str,
    model_used: str,
    total_cost_usd: float,
    items_analysed: int,
    sources_covered: int,
    track: str = "cognitive",
) -> int:
    """Insert a completed report. Returns its id."""
    sql = """
        INSERT INTO reports
            (report_cycle_id, report_tree, scenario_assessment, model_used,
             total_cost_usd, items_analysed, sources_covered, track)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_cycle_id) DO UPDATE
            SET report_tree = EXCLUDED.report_tree,
                scenario_assessment = EXCLUDED.scenario_assessment,
                total_cost_usd = EXCLUDED.total_cost_usd,
                track = EXCLUDED.track
        RETURNING id
    """
    return execute_returning(
        sql,
        (
            report_cycle_id,
            json.dumps(report_tree),
            scenario_assessment,
            model_used,
            total_cost_usd,
            items_analysed,
            sources_covered,
            track,
        ),
    )


def get_latest_cognitive_report() -> Optional[dict]:
    """Return the most recent cognitive-track report row, or None."""
    sql = """
        SELECT * FROM reports
        WHERE track = 'cognitive'
        ORDER BY created_at DESC LIMIT 1
    """
    rows = execute_query(sql)
    return rows[0] if rows else None


def get_latest_report() -> Optional[dict]:
    """Backward-compatible alias: latest cognitive report."""
    return get_latest_cognitive_report()


def insert_diffusion_wave1_output(
    report_cycle_id: str,
    fetched_item_id: int,
    source_weight: int,
    weight_justification: str,
    findings: list[dict],
    model_used: str,
    tokens_used: int,
    cost_usd: float,
) -> int:
    sql = """
        INSERT INTO diffusion_wave1_outputs
            (report_cycle_id, fetched_item_id, source_weight, weight_justification,
             findings, model_used, tokens_used, cost_usd)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """
    return execute_returning(
        sql,
        (
            report_cycle_id,
            fetched_item_id,
            source_weight,
            weight_justification,
            json.dumps(findings),
            model_used,
            tokens_used,
            cost_usd,
        ),
    )


def get_diffusion_wave1_outputs_for_cycle(report_cycle_id: str) -> list[dict]:
    sql = """
        SELECT w.id, w.report_cycle_id, w.fetched_item_id, w.source_weight,
               w.weight_justification, w.findings, w.model_used, w.tokens_used,
               w.cost_usd, w.created_at,
               fi.source_id, fi.title, fi.url, fi.published_at,
               s.name as source_name, s.category
        FROM diffusion_wave1_outputs w
        JOIN fetched_items fi ON fi.id = w.fetched_item_id
        JOIN sources s ON s.id = fi.source_id
        WHERE w.report_cycle_id = %s
        ORDER BY w.id ASC
    """
    return execute_query(sql, (report_cycle_id,))


def insert_diffusion_report(
    report_cycle_id: str,
    report_tree: dict,
    model_used: str,
    total_cost_usd: float,
    items_analysed: int,
    sources_covered: int,
) -> int:
    sql = """
        INSERT INTO diffusion_reports
            (report_cycle_id, report_tree, model_used, total_cost_usd, items_analysed, sources_covered)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_cycle_id) DO UPDATE
            SET report_tree = EXCLUDED.report_tree,
                total_cost_usd = EXCLUDED.total_cost_usd,
                items_analysed = EXCLUDED.items_analysed,
                sources_covered = EXCLUDED.sources_covered
        RETURNING id
    """
    return execute_returning(
        sql,
        (
            report_cycle_id,
            json.dumps(report_tree),
            model_used,
            total_cost_usd,
            items_analysed,
            sources_covered,
        ),
    )


# ── Fetch Logs ────────────────────────────────────────────────────────────────

def log_fetch(
    fetch_cycle_id: str,
    source_id: int,
    status: str,
    items_found: int = 0,
    error_message: Optional[str] = None,
    duration_seconds: Optional[float] = None,
) -> None:
    """Insert a fetch log entry."""
    sql = """
        INSERT INTO fetch_logs
            (fetch_cycle_id, source_id, status, items_found, error_message, duration_seconds)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    execute_non_query(sql, (fetch_cycle_id, source_id, status, items_found, error_message, duration_seconds))


def get_last_successful_fetch_at(source_id: int) -> Optional[datetime]:
    """Return timestamp of last successful fetch log for a source, or None."""
    sql = """
        SELECT created_at FROM fetch_logs
        WHERE source_id = %s AND status = 'success'
        ORDER BY created_at DESC LIMIT 1
    """
    rows = execute_query(sql, (source_id,))
    return rows[0]["created_at"] if rows else None


def get_consecutive_failures(source_id: int, n: int = 3) -> bool:
    """Return True if the source has failed n consecutive fetch cycles."""
    sql = """
        SELECT status FROM fetch_logs
        WHERE source_id = %s
        ORDER BY created_at DESC
        LIMIT %s
    """
    rows = execute_query(sql, (source_id, n))
    if len(rows) < n:
        return False
    return all(r["status"] == "error" for r in rows)


# ── Sources ───────────────────────────────────────────────────────────────────

def get_sources(active_only: bool = True) -> list[dict]:
    """Return list of source dicts."""
    if active_only:
        sql = "SELECT * FROM sources WHERE active = true ORDER BY id"
        return execute_query(sql)
    return execute_query("SELECT * FROM sources ORDER BY id")


def get_sources_for_fetch(active_only: bool = True, track_filter: str = "all") -> list[dict]:
    """
    Sources to fetch for this run.
    track_filter: 'all' | 'cognitive' | 'diffusion'
    """
    if track_filter == "all":
        return get_sources(active_only=active_only)
    parts: list[str] = ["SELECT * FROM sources WHERE"]
    cond: list[str] = []
    params: tuple = ()
    if active_only:
        cond.append("active = true")
    if track_filter == "cognitive":
        cond.append("track = 'cognitive'")
    elif track_filter == "diffusion":
        cond.append("(track = 'diffusion' OR id = ANY(%s))")
        params = (list(SHARED_DIFFUSION_SOURCE_IDS),)
    else:
        raise ValueError(f"Invalid track_filter: {track_filter!r}")
    parts.append(" AND ".join(cond))
    parts.append("ORDER BY id")
    sql = " ".join(parts)
    return execute_query(sql, params) if params else execute_query(sql)


def insert_source(
    name: str,
    category: str,
    fetch_method: str,
    url: str,
    weight_default: int,
    track: str = "cognitive",
) -> int:
    """Insert a source (idempotent by name). Returns its id."""
    sql = """
        INSERT INTO sources (name, category, fetch_method, url, weight_default, track)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (name) DO NOTHING
        RETURNING id
    """
    result = execute_returning(sql, (name, category, fetch_method, url, weight_default, track))
    if result is None:
        # Already exists — fetch existing id
        rows = execute_query("SELECT id FROM sources WHERE name = %s", (name,))
        return rows[0]["id"] if rows else None
    return result
