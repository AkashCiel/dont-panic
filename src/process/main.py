"""Main entry point for the report generation job (Wave 1 → Wave 2 → HTML)."""
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import get_config
from src.db.models import insert_report
from src.process.response_envelope import MissingContextHalt
from src.process.wave1 import run_wave1
from src.process.wave2 import run_wave2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def get_provider(config):
    """Instantiate the LLM provider from config."""
    provider_name = config.llm_provider.lower()
    if provider_name == "openai":
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for the OpenAI provider")
        from src.llm.openai_provider import OpenAIProvider
        return OpenAIProvider(api_key=config.openai_api_key, model=config.llm_model)
    else:
        raise ValueError(f"Unsupported LLM provider: {config.llm_provider!r}. Supported: openai")


def _write_report_json(report_cycle_id: str, scenario: str, report_tree: dict, total_cost: float, items: int) -> str:
    """Write the report JSON to output/latest_report.json for the HTML generator."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_dir = os.path.join(root, "output")
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "latest_report.json")

    payload = {
        "report_cycle_id": report_cycle_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scenario_assessment": scenario,
        "report_tree": report_tree,
        "total_cost_usd": total_cost,
        "items_analysed": items,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)

    logger.info(f"Report JSON written to {path}")
    return path


def run_processing() -> None:
    config = get_config()
    report_cycle_id = (
        f"report-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:8]}"
    )
    logger.info(f"Starting report cycle: {report_cycle_id}")

    provider = get_provider(config)
    overall_start = time.time()

    # ── Wave 1 ────────────────────────────────────────────────────────────────
    logger.info("=== Wave 1: Source-level analysis ===")
    wave1_start = time.time()
    try:
        wave1_summary = run_wave1(provider, report_cycle_id)
        wave1_duration = time.time() - wave1_start
        logger.info(
            f"Wave 1 complete: {wave1_summary['items_processed']} items, "
            f"{wave1_summary['claims_extracted']} claims, "
            f"${wave1_summary['cost_usd']:.4f}, "
            f"{wave1_duration / 60:.1f} min"
        )

        if config.telegram_bot_token:
            try:
                from src.notify.telegram import send_wave1_summary
                send_wave1_summary(
                    date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    items=wave1_summary["items_processed"],
                    sources=0,
                    claims=wave1_summary["claims_extracted"],
                    by_criterion=wave1_summary["by_criterion"],
                    cost=wave1_summary["cost_usd"],
                    duration_minutes=wave1_duration / 60,
                )
            except Exception as e:
                logger.warning(f"Wave 1 Telegram notification failed: {e}")

    except MissingContextHalt as e:
        logger.warning(
            "Cognitive pipeline halted: LLM reported missing context (track=%s). "
            "Inject missing context and restart manually. Detail: %s",
            e.track_name,
            e.detail[:500],
        )
        sys.exit(1)

    except Exception as e:
        logger.error(f"Wave 1 failed: {e}", exc_info=True)
        if config.telegram_bot_token:
            try:
                from src.notify.telegram import send_error
                send_error("Wave 1", str(e))
            except Exception:
                pass
        sys.exit(1)

    if wave1_summary["items_processed"] == 0:
        logger.warning("No items were processed in Wave 1 — skipping Wave 2")
        return

    # ── Wave 2 ────────────────────────────────────────────────────────────────
    logger.info("=== Wave 2: Synthesis ===")
    wave2_start = time.time()
    try:
        wave2_result = run_wave2(provider, report_cycle_id, wave1_summary)
        wave2_duration = time.time() - wave2_start
        logger.info(
            f"Wave 2 complete: scenario={wave2_result['scenario_assessment']}, "
            f"${wave2_result['cost_usd']:.4f}, "
            f"{wave2_duration / 60:.1f} min"
        )

        total_cost = wave1_summary["cost_usd"] + wave2_result["cost_usd"]

        # Save to database
        insert_report(
            report_cycle_id=report_cycle_id,
            report_tree=wave2_result["report_tree"],
            scenario_assessment=wave2_result["scenario_assessment"],
            model_used=config.llm_model,
            total_cost_usd=total_cost,
            items_analysed=wave1_summary["items_processed"],
            sources_covered=0,  # populated by wave2 internals in full implementation
        )

        # Write JSON for HTML generator
        _write_report_json(
            report_cycle_id=report_cycle_id,
            scenario=wave2_result["scenario_assessment"],
            report_tree=wave2_result["report_tree"],
            total_cost=total_cost,
            items=wave1_summary["items_processed"],
        )

        if config.telegram_bot_token:
            try:
                from src.notify.telegram import send_wave2_summary
                # GitHub Pages URL — will vary by repo; fallback to generic
                repo_owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "")
                repo_name = os.environ.get("GITHUB_REPOSITORY", "").split("/")[-1] if os.environ.get("GITHUB_REPOSITORY") else ""
                report_url = (
                    f"https://{repo_owner}.github.io/{repo_name}/"
                    if repo_owner and repo_name
                    else "https://github.com"
                )
                send_wave2_summary(
                    date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    scenario=wave2_result["scenario_assessment"],
                    report_url=report_url,
                    cost=wave2_result["cost_usd"],
                    duration_minutes=wave2_duration / 60,
                )
            except Exception as e:
                logger.warning(f"Wave 2 Telegram notification failed: {e}")

    except MissingContextHalt as e:
        logger.warning(
            "Cognitive pipeline halted: LLM reported missing context (track=%s). "
            "Inject missing context and restart manually. Detail: %s",
            e.track_name,
            e.detail[:500],
        )
        sys.exit(1)

    except Exception as e:
        logger.error(f"Wave 2 failed: {e}", exc_info=True)
        if config.telegram_bot_token:
            try:
                from src.notify.telegram import send_error
                send_error("Wave 2", str(e))
            except Exception:
                pass
        sys.exit(1)

    total_duration = time.time() - overall_start
    logger.info(f"Processing complete in {total_duration / 60:.1f} min, total cost ${wave1_summary['cost_usd'] + wave2_result['cost_usd']:.4f}")


if __name__ == "__main__":
    run_processing()
