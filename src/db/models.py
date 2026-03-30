"""Database operations — insert, query, and helper functions."""
import json
import logging
from datetime import datetime
from typing import Any, Optional

from src.db.connection import execute_query, execute_non_query, execute_returning, execute_many

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
    """Return unprocessed fetched_items ordered by fetched_at asc."""
    sql = """
        SELECT fi.id, fi.source_id, fi.external_id, fi.title, fi.content,
               fi.url, fi.published_at, fi.fetch_cycle_id,
               s.name as source_name, s.category, s.weight_default
        FROM fetched_items fi
        JOIN sources s ON s.id = fi.source_id
        WHERE fi.processed = false
        ORDER BY fi.fetched_at ASC
        LIMIT %s
    """
    return execute_query(sql, (limit,))


def mark_items_processed(item_ids: list[int]) -> None:
    """Set processed=true for the given item ids."""
    if not item_ids:
        return
    # Use ANY with a list converted to tuple
    sql = "UPDATE fetched_items SET processed = true WHERE id = ANY(%s)"
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
) -> int:
    """Insert a wave1 output record. Returns its id."""
    sql = """
        INSERT INTO wave1_outputs
            (report_cycle_id, fetched_item_id, source_weight, weight_justification,
             claims, model_used, tokens_used, cost_usd)
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
            json.dumps(claims),
            model_used,
            tokens_used,
            cost_usd,
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
        WHERE w.report_cycle_id = %s
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
) -> int:
    """Insert a completed report. Returns its id."""
    sql = """
        INSERT INTO reports
            (report_cycle_id, report_tree, scenario_assessment, model_used,
             total_cost_usd, items_analysed, sources_covered)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_cycle_id) DO UPDATE
            SET report_tree = EXCLUDED.report_tree,
                scenario_assessment = EXCLUDED.scenario_assessment,
                total_cost_usd = EXCLUDED.total_cost_usd
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
        ),
    )


def get_latest_report() -> Optional[dict]:
    """Return the most recent report row, or None."""
    sql = "SELECT * FROM reports ORDER BY created_at DESC LIMIT 1"
    rows = execute_query(sql)
    return rows[0] if rows else None


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


def insert_source(
    name: str,
    category: str,
    fetch_method: str,
    url: str,
    weight_default: int,
) -> int:
    """Insert a source (idempotent by name). Returns its id."""
    sql = """
        INSERT INTO sources (name, category, fetch_method, url, weight_default)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (name) DO NOTHING
        RETURNING id
    """
    result = execute_returning(sql, (name, category, fetch_method, url, weight_default))
    if result is None:
        # Already exists — fetch existing id
        rows = execute_query("SELECT id FROM sources WHERE name = %s", (name,))
        return rows[0]["id"] if rows else None
    return result
