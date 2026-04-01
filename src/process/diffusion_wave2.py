"""Diffusion Wave 2: synthesise findings into diffusion report tree JSON."""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from src.db.models import get_diffusion_wave1_outputs_for_cycle, get_latest_cognitive_report
from src.llm.provider import BatchRequest, LLMProvider
from src.process.diffusion_prompts import (
    build_diffusion_wave2_merge_prompt,
    build_diffusion_wave2_partial_prompt,
    build_diffusion_wave2_system_prompt,
    build_diffusion_wave2_user_prompt,
    format_cognitive_context_block,
)
from src.process.response_envelope import parse_envelope, unwrap_payload

logger = logging.getLogger(__name__)

TRACK_NAME = "diffusion"

MAX_FINDINGS_CHARS = 80_000

CASCADE_ORDER_LABELS = {
    0: "direct_channel_labs_to_individuals",
    1: "first_order_players",
    2: "institutional_consumers",
    3: "downstream_to_people",
}


def _normalise_findings(raw: Any) -> list[dict]:
    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return []
    return raw if isinstance(raw, list) else []


def _build_findings_document(wave1_outputs: list[dict]) -> str:
    """Flatten Wave 1 outputs into a text document for synthesis."""
    parts: list[str] = []
    for output in wave1_outputs:
        findings = _normalise_findings(output.get("findings"))
        source_name = output.get("source_name", "Unknown")
        sw = output.get("source_weight", 3)
        wj = output.get("weight_justification", "")
        parts.append(f"### Source: {source_name} (weight {sw})")
        if wj:
            parts.append(f"Weight justification: {wj}")
        for f in findings:
            if not isinstance(f, dict):
                continue
            co = f.get("cascade_order", "")
            cc = f.get("cascade_category", "")
            line = (
                f"- [order {co}] [{cc}] {f.get('finding', '')} "
                f"(confidence={f.get('confidence')}, Q={f.get('q1_q2_q3_relevance', '')})"
            )
            if f.get("notes"):
                line += f" — {f.get('notes')}"
            parts.append(line)
        parts.append("")
    return "\n".join(parts)


def _group_findings_by_order(wave1_outputs: list[dict]) -> dict[int, list[str]]:
    grouped: dict[int, list[str]] = {0: [], 1: [], 2: [], 3: []}
    for output in wave1_outputs:
        findings = _normalise_findings(output.get("findings"))
        source_name = output.get("source_name", "Unknown")
        for f in findings:
            if not isinstance(f, dict):
                continue
            try:
                co = int(f.get("cascade_order", -1))
            except (TypeError, ValueError):
                continue
            if co not in grouped:
                continue
            line = f"[{source_name}] {f.get('finding', '')}"
            grouped[co].append(line)
    return grouped


def run_diffusion_wave2(provider: LLMProvider, report_cycle_id: str, wave1_summary: dict) -> dict:
    wave1_outputs = get_diffusion_wave1_outputs_for_cycle(report_cycle_id)
    if not wave1_outputs:
        raise ValueError(f"No diffusion Wave 1 outputs for cycle {report_cycle_id}")

    cognitive_row = get_latest_cognitive_report()
    cognitive_block = format_cognitive_context_block(cognitive_row)

    findings_document = _build_findings_document(wave1_outputs)
    sources_covered = len({o.get("source_id") for o in wave1_outputs if o.get("source_id")})
    now = datetime.now(timezone.utc)
    date_range = f"up to {now.strftime('%Y-%m-%d')}"

    system_prompt = build_diffusion_wave2_system_prompt()

    if len(findings_document) > MAX_FINDINGS_CHARS:
        grouped = _group_findings_by_order(wave1_outputs)
        if any(grouped.values()):
            logger.info(
                f"Findings document is {len(findings_document):,} chars — splitting diffusion Wave 2 by cascade order"
            )
            return _run_diffusion_wave2_split(
                provider=provider,
                report_cycle_id=report_cycle_id,
                wave1_outputs=wave1_outputs,
                system_prompt=system_prompt,
                cognitive_block=cognitive_block,
                date_range=date_range,
                total_items=wave1_summary.get("items_processed", 0),
                sources_covered=sources_covered,
            )
        logger.warning("Findings document oversized but no cascade groups — truncating for single Wave 2 call")
        findings_document = findings_document[:MAX_FINDINGS_CHARS]

    user_prompt = build_diffusion_wave2_user_prompt(
        report_cycle_id=report_cycle_id,
        date_range=date_range,
        total_items=wave1_summary.get("items_processed", 0),
        sources_covered=sources_covered,
        cognitive_context_block=cognitive_block,
        findings_document=findings_document,
    )

    custom_id = f"dw2-main-{str(uuid.uuid4())[:12]}"
    batch_requests = [
        BatchRequest(
            custom_id=custom_id,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=8192,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
    ]

    logger.info("Submitting diffusion Wave 2 batch (single call)")
    batch_id = provider.submit_batch(batch_requests)
    results = provider.wait_for_batch(batch_id, poll_interval_seconds=30)
    result = results[0]
    if result.error:
        raise RuntimeError(f"Diffusion Wave 2 failed: {result.error}")

    try:
        parsed = parse_envelope(result.content)
        report_tree = unwrap_payload(parsed, TRACK_NAME)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Diffusion Wave 2 JSON parse failed: {e}\n{result.content[:500]}") from e

    return {
        "report_tree": report_tree,
        "cost_usd": result.cost_usd,
        "batch_id": batch_id,
        "tokens_used": result.tokens_input + result.tokens_output,
    }


def _run_diffusion_wave2_split(
    provider: LLMProvider,
    report_cycle_id: str,
    wave1_outputs: list[dict],
    system_prompt: str,
    cognitive_block: str,
    date_range: str,
    total_items: int,
    sources_covered: int,
) -> dict:
    grouped = _group_findings_by_order(wave1_outputs)
    batch_requests: list[BatchRequest] = []

    for order, lines in grouped.items():
        if not lines:
            continue
        label = CASCADE_ORDER_LABELS.get(order, f"order_{order}")
        subset = "\n".join(lines[:2000])
        custom_id = f"dw2-p-{order}-{str(uuid.uuid4())[:8]}"
        batch_requests.append(
            BatchRequest(
                custom_id=custom_id,
                system_prompt=system_prompt,
                user_prompt=build_diffusion_wave2_partial_prompt(label, subset, cognitive_block),
                max_tokens=4096,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
        )

    if not batch_requests:
        raise RuntimeError("No cascade groups to run for split Wave 2")

    batch_id_1 = provider.submit_batch(batch_requests)
    partial_results = provider.wait_for_batch(batch_id_1, poll_interval_seconds=30)

    partial_docs: list[dict[str, Any]] = []
    total_cost = 0.0
    for r in partial_results:
        total_cost += r.cost_usd
        if r.error:
            logger.error(f"Partial cascade failed: {r.error}")
            continue
        try:
            parsed = parse_envelope(r.content)
            partial_docs.append(unwrap_payload(parsed, TRACK_NAME))
        except json.JSONDecodeError as e:
            logger.error(f"Partial JSON parse failed: {e}")

    merge_prompt = build_diffusion_wave2_merge_prompt(
        partial_docs,
        cognitive_block,
        {
            "report_cycle_id": report_cycle_id,
            "date_range": date_range,
            "total_items": total_items,
            "sources_covered": sources_covered,
        },
    )
    merge_id = f"dw2-merge-{str(uuid.uuid4())[:12]}"
    batch_id_2 = provider.submit_batch(
        [
            BatchRequest(
                custom_id=merge_id,
                system_prompt=system_prompt,
                user_prompt=merge_prompt,
                max_tokens=8192,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
        ]
    )
    merge_results = provider.wait_for_batch(batch_id_2, poll_interval_seconds=30)
    mr = merge_results[0]
    total_cost += mr.cost_usd
    if mr.error:
        raise RuntimeError(f"Diffusion Wave 2 merge failed: {mr.error}")
    try:
        parsed = parse_envelope(mr.content)
        report_tree = unwrap_payload(parsed, TRACK_NAME)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Merge JSON parse failed: {e}") from e

    return {
        "report_tree": report_tree,
        "cost_usd": total_cost,
        "batch_id": f"{batch_id_1},{batch_id_2}",
        "tokens_used": mr.tokens_input + mr.tokens_output,
    }
