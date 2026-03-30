"""Database connection management using psycopg2 connection pool."""
import logging
from contextlib import contextmanager
from typing import Any, Callable, Optional, TypeVar

import psycopg2
import psycopg2.extras
import psycopg2.pool

logger = logging.getLogger(__name__)

_pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None

T = TypeVar("T")

# How many times to try getting a live connection from the pool (stale ones are dropped).
_MAX_CHECKOUT_ATTEMPTS = 5


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


def _checkout_valid_connection(pool: psycopg2.pool.ThreadedConnectionPool):
    """
    Take a connection from the pool and ensure it talks to the server.

    Idle connections (e.g. after long OpenAI batch waits) may be closed by Neon
    or the network; those must not be returned to the pool as healthy.
    """
    last_exc: Optional[BaseException] = None
    for attempt in range(_MAX_CHECKOUT_ATTEMPTS):
        conn = pool.getconn()
        try:
            if getattr(conn, "closed", 0) != 0:
                pool.putconn(conn, close=True)
                continue
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            return conn
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            last_exc = e
            logger.warning(
                "Discarding stale pooled connection (attempt %s/%s): %s",
                attempt + 1,
                _MAX_CHECKOUT_ATTEMPTS,
                e,
            )
            try:
                pool.putconn(conn, close=True)
            except Exception:
                pass
    raise RuntimeError(
        "Could not obtain a valid database connection after several attempts"
    ) from last_exc


@contextmanager
def get_connection():
    """Context manager that acquires and releases a connection from the pool."""
    pool = _get_pool()
    conn = _checkout_valid_connection(pool)
    discard = False
    try:
        yield conn
        conn.commit()
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        discard = isinstance(e, (psycopg2.OperationalError, psycopg2.InterfaceError))
        if discard:
            logger.warning("DB error during operation; discarding pooled connection: %s", e)
        raise
    finally:
        try:
            if discard:
                pool.putconn(conn, close=True)
            else:
                pool.putconn(conn)
        except Exception:
            pass


def _retry_on_operational_error(func: Callable[[], T]) -> T:
    """Run once; on lost connection, run again with a fresh checkout."""
    try:
        return func()
    except psycopg2.OperationalError as e:
        logger.warning("Retrying database operation after OperationalError: %s", e)
        return func()


def execute_query(sql: str, params: Optional[tuple] = None) -> list[dict]:
    """Execute a SELECT query and return results as list of dicts."""

    def _do() -> list[dict]:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, params)
                return [dict(row) for row in cur.fetchall()]

    return _retry_on_operational_error(_do)


def execute_non_query(sql: str, params: Optional[tuple] = None) -> int:
    """Execute an INSERT/UPDATE/DELETE and return rowcount."""

    def _do() -> int:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.rowcount

    return _retry_on_operational_error(_do)


def execute_returning(sql: str, params: Optional[tuple] = None) -> Optional[Any]:
    """Execute an INSERT ... RETURNING and return the first column of the first row."""

    def _do() -> Optional[Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                row = cur.fetchone()
                return row[0] if row else None

    return _retry_on_operational_error(_do)


def execute_many(sql: str, params_list: list[tuple]) -> int:
    """Execute a batch insert/update and return total rowcount."""
    if not params_list:
        return 0

    def _do() -> int:
        with get_connection() as conn:
            with conn.cursor() as cur:
                psycopg2.extras.execute_batch(cur, sql, params_list)
                return cur.rowcount

    return _retry_on_operational_error(_do)
