"""Diffusion track: Wave 1 → Wave 2 → JSON for HTML generator."""
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import get_config
from src.db.models import get_diffusion_wave1_outputs_for_cycle, insert_diffusion_report
from src.process.diffusion_wave1 import run_diffusion_wave1
from src.process.diffusion_wave2 import run_diffusion_wave2
from src.process.response_envelope import MissingContextHalt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def get_provider(config):
    provider_name = config.llm_provider.lower()
    if provider_name == "openai":
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for the OpenAI provider")
        from src.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(api_key=config.openai_api_key, model=config.llm_model)
    raise ValueError(f"Unsupported LLM provider: {config.llm_provider!r}. Supported: openai")


def _write_diffusion_report_json(
    report_cycle_id: str,
    report_tree: dict,
    total_cost: float,
    items: int,
    sources_covered: int,
) -> str:
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_dir = os.path.join(root, "output")
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "latest_diffusion_report.json")
    payload = {
        "report_cycle_id": report_cycle_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "report_tree": report_tree,
        "total_cost_usd": total_cost,
        "items_analysed": items,
        "sources_covered": sources_covered,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    logger.info(f"Diffusion report JSON written to {path}")
    return path


def run_diffusion_processing() -> None:
    config = get_config()
    report_cycle_id = (
        f"diffusion-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:8]}"
    )
    logger.info(f"Starting diffusion report cycle: {report_cycle_id}")

    provider = get_provider(config)
    overall_start = time.time()

    logger.info("=== Diffusion Wave 1 ===")
    wave1_start = time.time()
    try:
        wave1_summary = run_diffusion_wave1(provider, report_cycle_id)
        wave1_duration = time.time() - wave1_start
        logger.info(
            f"Diffusion Wave 1: {wave1_summary['items_processed']} items queued, "
            f"{wave1_summary['findings_extracted']} findings, ${wave1_summary['cost_usd']:.4f}, "
            f"{wave1_duration / 60:.1f} min"
        )
        if config.telegram_bot_token:
            try:
                from src.notify.telegram import send_diffusion_wave1_summary

                send_diffusion_wave1_summary(
                    date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    items=wave1_summary["items_processed"],
                    findings=wave1_summary["findings_extracted"],
                    cost=wave1_summary["cost_usd"],
                    duration_minutes=wave1_duration / 60,
                )
            except Exception as e:
                logger.warning(f"Telegram diffusion Wave 1 notification failed: {e}")
    except MissingContextHalt as e:
        logger.warning(
            "Diffusion pipeline halted: missing context (track=%s). Restart manually after fixing. %s",
            e.track_name,
            e.detail[:500],
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"Diffusion Wave 1 failed: {e}", exc_info=True)
        if config.telegram_bot_token:
            try:
                from src.notify.telegram import send_error

                send_error("Diffusion Wave 1", str(e))
            except Exception:
                pass
        sys.exit(1)

    w1_rows = get_diffusion_wave1_outputs_for_cycle(report_cycle_id)
    if not w1_rows:
        logger.warning("No diffusion Wave 1 outputs persisted — skipping Wave 2")
        return

    logger.info("=== Diffusion Wave 2 ===")
    wave2_start = time.time()
    try:
        wave2_result = run_diffusion_wave2(provider, report_cycle_id, wave1_summary)
        wave2_duration = time.time() - wave2_start
        total_cost = wave1_summary["cost_usd"] + wave2_result["cost_usd"]
        wave1_outputs = get_diffusion_wave1_outputs_for_cycle(report_cycle_id)
        sources_covered = len({o.get("source_id") for o in wave1_outputs if o.get("source_id")})

        insert_diffusion_report(
            report_cycle_id=report_cycle_id,
            report_tree=wave2_result["report_tree"],
            model_used=config.llm_model,
            total_cost_usd=total_cost,
            items_analysed=wave1_summary["items_processed"],
            sources_covered=sources_covered,
        )

        _write_diffusion_report_json(
            report_cycle_id=report_cycle_id,
            report_tree=wave2_result["report_tree"],
            total_cost=total_cost,
            items=wave1_summary["items_processed"],
            sources_covered=sources_covered,
        )

        logger.info(
            f"Diffusion Wave 2 complete: ${wave2_result['cost_usd']:.4f}, {wave2_duration / 60:.1f} min"
        )

        if config.telegram_bot_token:
            try:
                from src.notify.telegram import send_diffusion_wave2_summary

                repo_owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "")
                repo_name = (
                    os.environ.get("GITHUB_REPOSITORY", "").split("/")[-1]
                    if os.environ.get("GITHUB_REPOSITORY")
                    else ""
                )
                base = (
                    f"https://{repo_owner}.github.io/{repo_name}/"
                    if repo_owner and repo_name
                    else "https://github.com"
                )
                report_url = base + "diffusion/"
                send_diffusion_wave2_summary(
                    date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    report_url=report_url,
                    cost=wave2_result["cost_usd"],
                    duration_minutes=wave2_duration / 60,
                )
            except Exception as e:
                logger.warning(f"Telegram diffusion Wave 2 notification failed: {e}")

    except MissingContextHalt as e:
        logger.warning(
            "Diffusion pipeline halted: missing context (track=%s). Restart manually after fixing. %s",
            e.track_name,
            e.detail[:500],
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"Diffusion Wave 2 failed: {e}", exc_info=True)
        if config.telegram_bot_token:
            try:
                from src.notify.telegram import send_error

                send_error("Diffusion Wave 2", str(e))
            except Exception:
                pass
        sys.exit(1)

    total_duration = time.time() - overall_start
    logger.info(f"Diffusion processing complete in {total_duration / 60:.1f} min")


if __name__ == "__main__":
    run_diffusion_processing()
