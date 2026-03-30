"""Main entry point for the daily fetch job."""
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import get_config
from src.db.models import get_sources, get_consecutive_failures, insert_fetched_item, log_fetch
from src.fetch.api_fetcher import fetch_api_source
from src.fetch.csv_fetcher import fetch_csv_source
from src.fetch.graphql_fetcher import fetch_lesswrong
from src.fetch.openreview_fetcher import fetch_openreview
from src.fetch.rss_fetcher import fetch_rss
from src.fetch.scrape_fetcher import fetch_scrape_source

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def _get_fetcher(fetch_method: str):
    """Return the correct fetcher lambda for a fetch method."""
    return {
        "rss": lambda source, cycle_id, cfg: fetch_rss(source, cycle_id),
        "rest_api": lambda source, cycle_id, cfg: fetch_api_source(source, cycle_id, cfg),
        "csv": lambda source, cycle_id, cfg: fetch_csv_source(source, cycle_id),
        "graphql": lambda source, cycle_id, cfg: fetch_lesswrong(source, cycle_id),
        "sdk": lambda source, cycle_id, cfg: fetch_openreview(
            source, cycle_id, cfg.openreview_username, cfg.openreview_password
        ),
        "scrape": lambda source, cycle_id, cfg: fetch_scrape_source(source, cycle_id),
    }.get(fetch_method)


def run_fetch_cycle() -> list[dict]:
    config = get_config()
    fetch_cycle_id = (
        f"fetch-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:8]}"
    )
    logger.info(f"Starting fetch cycle: {fetch_cycle_id}")

    sources = get_sources(active_only=True)
    results: list[dict] = []

    for source in sources:
        source_id = source["id"]
        source_name = source["name"]
        fetch_method = source["fetch_method"]
        weight = source["weight_default"]

        start_time = time.time()
        items_found = 0
        status = "success"
        error_message = None

        fetcher = _get_fetcher(fetch_method)
        if not fetcher:
            status = "error"
            error_message = f"Unknown fetch method: {fetch_method}"
            logger.error(f"Source {source_name}: {error_message}")
        else:
            try:
                raw_items = fetcher(source, fetch_cycle_id, config)
                high_signal_titles: list[str] = []

                for item in raw_items:
                    inserted_id = insert_fetched_item(
                        source_id=source_id,
                        external_id=str(item["external_id"])[:500],
                        title=str(item.get("title", ""))[:2000],
                        content=str(item.get("content", ""))[:10000],
                        url=str(item.get("url", ""))[:2000],
                        published_at=item.get("published_at"),
                        fetch_cycle_id=fetch_cycle_id,
                    )
                    if inserted_id is not None:
                        items_found += 1
                        if weight >= 4:
                            high_signal_titles.append(item.get("title", ""))

                # Alert on new high-signal items
                if high_signal_titles and config.telegram_bot_token:
                    try:
                        from src.notify.telegram import send_high_signal_alert
                        for title in high_signal_titles[:3]:
                            send_high_signal_alert(source_name, weight, title)
                    except Exception as te:
                        logger.warning(f"Telegram high-signal alert failed: {te}")

                logger.info(f"  {source_name}: {items_found} new items (of {len(raw_items)} fetched)")

            except Exception as e:
                status = "error"
                error_message = str(e)
                logger.error(f"Source {source_name} failed: {e}", exc_info=True)

        duration = round(time.time() - start_time, 2)
        log_fetch(fetch_cycle_id, source_id, status, items_found, error_message, duration)

        # Flag repeated failures
        if status == "error":
            try:
                if get_consecutive_failures(source_id, n=3):
                    logger.warning(f"Source {source_name} has failed 3 consecutive cycles — check configuration")
            except Exception:
                pass

        results.append({
            "source_name": source_name,
            "status": status,
            "items_found": items_found,
            "error_message": error_message,
        })

    # Send Telegram summary
    if config.telegram_bot_token:
        try:
            from src.notify.telegram import send_fetch_summary
            send_fetch_summary(fetch_cycle_id, results)
        except Exception as e:
            logger.error(f"Failed to send Telegram fetch summary: {e}")

    n_success = sum(1 for r in results if r["status"] == "success")
    total_new = sum(r["items_found"] for r in results)
    logger.info(
        f"Fetch cycle complete: {n_success}/{len(results)} sources OK, {total_new} total new items"
    )
    return results


if __name__ == "__main__":
    run_fetch_cycle()
