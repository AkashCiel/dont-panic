"""Database connection management using psycopg2 connection pool."""
import logging
from contextlib import contextmanager
from typing import Any, Optional

import psycopg2
import psycopg2.extras
import psycopg2.pool

logger = logging.getLogger(__name__)

_pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None


def _get_pool() -> psycopg2.pool.ThreadedConnectionPool:
    """Initialize and return the connection pool (lazy)."""
    global _pool
    if _pool is None:
        from src.config import get_config
        config = get_config()
        try:
            _pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=config.database_url,
            )
            logger.info("Database connection pool initialized")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize database connection pool: {e}") from e
    return _pool


@contextmanager
def get_connection():
    """Context manager that acquires and releases a connection from the pool."""
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def execute_query(sql: str, params: Optional[tuple] = None) -> list[dict]:
    """Execute a SELECT query and return results as list of dicts."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]


def execute_non_query(sql: str, params: Optional[tuple] = None) -> int:
    """Execute an INSERT/UPDATE/DELETE and return rowcount."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.rowcount


def execute_returning(sql: str, params: Optional[tuple] = None) -> Optional[Any]:
    """Execute an INSERT ... RETURNING and return the first column of the first row."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return row[0] if row else None


def execute_many(sql: str, params_list: list[tuple]) -> int:
    """Execute a batch insert/update and return total rowcount."""
    if not params_list:
        return 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_batch(cur, sql, params_list)
            return cur.rowcount
