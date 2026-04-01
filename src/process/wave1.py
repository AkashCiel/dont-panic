"""Wave 1: Source-level claim extraction from fetched items."""
import json
import logging
import uuid
from typing import Any

from src.db.models import (
    get_sources,
    get_unprocessed_items,
    insert_wave1_output,
    mark_items_processed,
)
from src.llm.provider import BatchRequest, LLMProvider
from src.process.prompts import build_wave1_system_prompt, build_wave1_user_prompt
from src.process.response_envelope import parse_envelope, unwrap_payload

logger = logging.getLogger(__name__)

BATCH_SIZE = 12  # items per Wave 1 API call (for high-volume sources like arXiv)
TRACK_NAME = "cognitive"


def run_wave1(provider: LLMProvider, report_cycle_id: str) -> dict:
    """
    Run Wave 1 analysis on all unprocessed fetched items.

    Steps:
    1. Fetch all unprocessed items from the database.
    2. Group by source_id.
    3. Build one BatchRequest per source-batch (up to BATCH_SIZE items).
    4. Submit all as one OpenAI Batch API job.
    5. Wait for completion.
    6. Parse results, save to wave1_outputs, mark items processed.

    Returns a summary dict.
    """
    items = get_unprocessed_items(limit=2000)
    if not items:
        logger.info("No unprocessed items for Wave 1 — nothing to do")
        return {
            "items_processed": 0,
            "claims_extracted": 0,
            "by_criterion": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            "cost_usd": 0.0,
            "batch_id": None,
        }

    # Build source lookup
    sources_list = get_sources(active_only=False)
    sources_by_id: dict[int, dict] = {s["id"]: s for s in sources_list}

    # Group items by source_id
    by_source: dict[int, list[dict]] = {}
    for item in items:
        by_source.setdefault(item["source_id"], []).append(item)

    system_prompt = build_wave1_system_prompt()
    batch_requests: list[BatchRequest] = []
    request_meta: dict[str, dict[str, Any]] = {}  # custom_id → {source_id, item_ids}

    for source_id, source_items in by_source.items():
        source = sources_by_id.get(source_id, {"name": f"Source {source_id}", "category": "unknown", "weight_default": 3})
        # Chunk large sources
        for batch_start in range(0, len(source_items), BATCH_SIZE):
            batch_items = source_items[batch_start : batch_start + BATCH_SIZE]
            custom_id = f"w1-{source_id}-{batch_start}-{str(uuid.uuid4())[:8]}"
            user_prompt = build_wave1_user_prompt(
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

    logger.info(f"Submitting Wave 1 batch: {len(batch_requests)} requests for {len(by_source)} sources")
    batch_id = provider.submit_batch(batch_requests)
    results = provider.wait_for_batch(batch_id, poll_interval_seconds=30)

    # Process results
    total_claims = 0
    by_criterion: dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    total_cost = 0.0
    all_item_ids: list[int] = []

    for result in results:
        meta = request_meta.get(result.custom_id, {})
        item_ids = meta.get("item_ids", [])
        total_cost += result.cost_usd

        if result.error:
            logger.error(f"Wave 1 request {result.custom_id} errored: {result.error}")
            continue

        try:
            parsed = parse_envelope(result.content)
            payload = unwrap_payload(parsed, TRACK_NAME)
        except json.JSONDecodeError as e:
            logger.error(f"Wave 1 JSON parse failed for {result.custom_id}: {e}\nContent: {result.content[:300]}")
            continue

        claims = payload.get("claims", [])
        source_weight = int(payload.get("source_weight", 3))
        weight_justification = payload.get("weight_justification", "")
        model_name = getattr(provider, "model", "unknown")

        # Insert one wave1_output row per item_id (shares the claims)
        cost_per_item = result.cost_usd / max(len(item_ids), 1)
        for item_id in item_ids:
            insert_wave1_output(
                report_cycle_id=report_cycle_id,
                fetched_item_id=item_id,
                source_weight=source_weight,
                weight_justification=weight_justification,
                claims=claims,
                model_used=model_name,
                tokens_used=(result.tokens_input + result.tokens_output) // max(len(item_ids), 1),
                cost_usd=cost_per_item,
            )

        for claim in claims:
            criterion = claim.get("criterion")
            if criterion in by_criterion:
                by_criterion[criterion] += 1
        total_claims += len(claims)
        all_item_ids.extend(item_ids)

    # Mark items as processed
    if all_item_ids:
        mark_items_processed(all_item_ids)
        logger.info(f"Marked {len(all_item_ids)} items as processed")

    return {
        "items_processed": len(items),
        "claims_extracted": total_claims,
        "by_criterion": by_criterion,
        "cost_usd": total_cost,
        "batch_id": batch_id,
    }
