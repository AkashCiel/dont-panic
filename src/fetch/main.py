"""Main entry point for the daily fetch job."""
import argparse
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import get_config
from src.db.models import (
    get_consecutive_failures,
    get_last_successful_fetch_at,
    get_sources_for_fetch,
    insert_fetched_item,
    log_fetch,
)
from src.fetch.api_fetcher import fetch_api_source
from src.fetch.cloudflare_radar_fetcher import fetch_cloudflare_radar
from src.fetch.csv_fetcher import fetch_csv_source
from src.fetch.economic_index_fetcher import fetch_economic_index
from src.fetch.gov_fetchers import fetch_sam_gov, fetch_ted_eu, fetch_usaspending
from src.fetch.graphql_fetcher import fetch_lesswrong
from src.fetch.openreview_fetcher import fetch_openreview
from src.fetch.rss_fetcher import fetch_rss, fetch_rss_ai_keywords
from src.fetch.scrape_fetcher import fetch_scrape_source
from src.fetch.sec_edgar_fetcher import fetch_sec_edgar

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def _get_fetcher(fetch_method: str):
    """Return a callable (source, cycle_id, config) -> list[dict]."""
    return {
        "rss": lambda source, cycle_id, cfg: fetch_rss(source, cycle_id),
        "rss_ai": lambda source, cycle_id, cfg: fetch_rss_ai_keywords(source, cycle_id),
        "rest_api": lambda source, cycle_id, cfg: fetch_api_source(source, cycle_id, cfg),
        "csv": lambda source, cycle_id, cfg: fetch_csv_source(source, cycle_id),
        "graphql": lambda source, cycle_id, cfg: fetch_lesswrong(source, cycle_id),
        "sdk": lambda source, cycle_id, cfg: fetch_openreview(
            source, cycle_id, cfg.openreview_username, cfg.openreview_password
        ),
        "scrape": lambda source, cycle_id, cfg: fetch_scrape_source(source, cycle_id),
        "sec_edgar": lambda source, cycle_id, cfg: fetch_sec_edgar(source, cycle_id),
        "sam_gov": lambda source, cycle_id, cfg: fetch_sam_gov(source, cycle_id, cfg.sam_gov_api_key),
        "usaspending": lambda source, cycle_id, cfg: fetch_usaspending(source, cycle_id),
        "ted_eu": lambda source, cycle_id, cfg: fetch_ted_eu(source, cycle_id),
        "cloudflare_radar": lambda source, cycle_id, cfg: fetch_cloudflare_radar(
            source, cycle_id, cfg.cloudflare_api_token
        ),
        "economic_index": lambda source, cycle_id, cfg: fetch_economic_index(source, cycle_id),
    }.get(fetch_method)


def _should_skip_periodic_fetch(source_id: int, min_interval_days: int) -> bool:
    last = get_last_successful_fetch_at(source_id)
    if not last:
        return False
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    return (now - last) < timedelta(days=min_interval_days)


def run_fetch_cycle(track_filter: str = "all") -> list[dict]:
    config = get_config()
    fetch_cycle_id = (
        f"fetch-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:8]}"
    )
    logger.info(f"Starting fetch cycle: {fetch_cycle_id} (track={track_filter})")

    sources = get_sources_for_fetch(active_only=True, track_filter=track_filter)
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

        if source_id == 26 and _should_skip_periodic_fetch(26, 7):
            logger.info(f"Skipping {source_name} — successful fetch within last 7 days")
            duration = round(time.time() - start_time, 2)
            log_fetch(fetch_cycle_id, source_id, "success", 0, None, duration)
            results.append({
                "source_name": source_name,
                "status": status,
                "items_found": 0,
                "error_message": None,
            })
            continue

        if source_id == 32 and _should_skip_periodic_fetch(32, 30):
            logger.info(f"Skipping {source_name} — successful fetch within last 30 days")
            duration = round(time.time() - start_time, 2)
            log_fetch(fetch_cycle_id, source_id, "success", 0, None, duration)
            results.append({
                "source_name": source_name,
                "status": status,
                "items_found": 0,
                "error_message": None,
            })
            continue

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

        if status == "error":
            try:
                if get_consecutive_failures(source_id, n=3):
                    logger.warning(
                        f"Source {source_name} has failed 3 consecutive cycles — check configuration"
                    )
            except Exception:
                pass

        results.append({
            "source_name": source_name,
            "status": status,
            "items_found": items_found,
            "error_message": error_message,
        })

    if config.telegram_bot_token:
        try:
            if track_filter == "diffusion":
                from src.notify.telegram import send_diffusion_fetch_summary

                send_diffusion_fetch_summary(fetch_cycle_id, results)
            else:
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
    parser = argparse.ArgumentParser(description="Fetch from configured sources")
    parser.add_argument(
        "--track",
        choices=["all", "cognitive", "diffusion"],
        default="all",
        help="Which sources to fetch (default: all)",
    )
    args = parser.parse_args()
    run_fetch_cycle(track_filter=args.track)
