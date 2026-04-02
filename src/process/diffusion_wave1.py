"""Diffusion Wave 1: extract findings from fetched items (diffusion + shared sources)."""
import json
import logging
import uuid
from typing import Any

from src.db.models import (
    get_sources,
    get_unprocessed_diffusion_items,
    insert_diffusion_wave1_output,
    mark_items_diffusion_processed,
)
from src.llm.provider import BatchRequest, LLMProvider
from src.process.diffusion_prompts import (
    build_diffusion_wave1_system_prompt,
    build_diffusion_wave1_user_prompt,
)
from src.process.response_envelope import parse_envelope, unwrap_payload

logger = logging.getLogger(__name__)

BATCH_SIZE = 12
TRACK_NAME = "diffusion"


def run_diffusion_wave1(provider: LLMProvider, report_cycle_id: str) -> dict:
    items = get_unprocessed_diffusion_items(limit=2000)
    if not items:
        logger.info("No unprocessed items for diffusion Wave 1 — nothing to do")
        return {
            "items_processed": 0,
            "findings_extracted": 0,
            "by_cascade_order": {0: 0, 1: 0, 2: 0, 3: 0},
            "cost_usd": 0.0,
            "batch_id": None,
        }

    sources_list = get_sources(active_only=False)
    sources_by_id: dict[int, dict] = {s["id"]: s for s in sources_list}

    by_source: dict[int, list[dict]] = {}
    for item in items:
        by_source.setdefault(item["source_id"], []).append(item)

    system_prompt = build_diffusion_wave1_system_prompt()
    batch_requests: list[BatchRequest] = []
    request_meta: dict[str, dict[str, Any]] = {}

    for source_id, source_items in by_source.items():
        source = sources_by_id.get(
            source_id,
            {"name": f"Source {source_id}", "category": "unknown", "weight_default": 3},
        )
        for batch_start in range(0, len(source_items), BATCH_SIZE):
            batch_items = source_items[batch_start : batch_start + BATCH_SIZE]
            custom_id = f"dw1-{source_id}-{batch_start}-{str(uuid.uuid4())[:8]}"
            user_prompt = build_diffusion_wave1_user_prompt(
                source_id=source_id,
                source_name=source.get("name", f"Source {source_id}"),
                category=source.get("category", "unknown"),
                weight_default=source.get("weight_default", 3),
                items=batch_items,
            )
            batch_requests.append(
                BatchRequest(
                    custom_id=custom_id,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=4096,
                    temperature=0.1,
                    response_format={"type": "json_object"},
                )
            )
            request_meta[custom_id] = {
                "source_id": source_id,
                "item_ids": [item["id"] for item in batch_items],
            }

    logger.info(f"Submitting diffusion Wave 1 batch: {len(batch_requests)} requests")
    batch_id = provider.submit_batch(batch_requests)
    results = provider.wait_for_batch(batch_id, poll_interval_seconds=30)

    total_findings = 0
    by_cascade: dict[int, int] = {0: 0, 1: 0, 2: 0, 3: 0}
    total_cost = 0.0
    all_item_ids: list[int] = []

    for result in results:
        meta = request_meta.get(result.custom_id, {})
        item_ids = meta.get("item_ids", [])
        total_cost += result.cost_usd

        if result.error:
            logger.error(f"Diffusion Wave 1 {result.custom_id} errored: {result.error}")
            continue

        try:
            parsed = parse_envelope(result.content)
            payload = unwrap_payload(parsed, TRACK_NAME)
        except json.JSONDecodeError as e:
            logger.error(f"Diffusion Wave 1 JSON parse failed: {e}\n{result.content[:400]}")
            continue

        findings = payload.get("findings") or []
        if not isinstance(findings, list):
            findings = []
        source_weight = int(payload.get("source_weight", 3))
        weight_justification = str(payload.get("weight_justification", ""))
        model_name = getattr(provider, "model", "unknown")

        cost_per_item = result.cost_usd / max(len(item_ids), 1)
        for item_id in item_ids:
            insert_diffusion_wave1_output(
                report_cycle_id=report_cycle_id,
                fetched_item_id=item_id,
                source_weight=source_weight,
                weight_justification=weight_justification,
                findings=findings,
                model_used=model_name,
                tokens_used=(result.tokens_input + result.tokens_output) // max(len(item_ids), 1),
                cost_usd=cost_per_item,
            )

        for f in findings:
            if not isinstance(f, dict):
                continue
            co = f.get("cascade_order")
            try:
                co = int(co)
            except (TypeError, ValueError):
                continue
            if co in by_cascade:
                by_cascade[co] += 1
        total_findings += len(findings)
        all_item_ids.extend(item_ids)

    if all_item_ids:
        mark_items_diffusion_processed(all_item_ids)
        logger.info(f"Marked {len(all_item_ids)} items as diffusion_processed")

    return {
        "items_processed": len(items),
        "findings_extracted": total_findings,
        "by_cascade_order": by_cascade,
        "cost_usd": total_cost,
        "batch_id": batch_id,
    }
