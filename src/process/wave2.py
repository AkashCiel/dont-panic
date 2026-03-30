"""Wave 2: Synthesis — aggregate Wave 1 claims into the final report tree."""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from src.db.models import get_wave1_outputs_for_cycle
from src.llm.provider import BatchRequest, LLMProvider
from src.process.prompts import build_wave2_system_prompt, build_wave2_user_prompt

logger = logging.getLogger(__name__)

# If the claims document exceeds this many characters, split by criterion
MAX_CLAIMS_CHARS = 80_000

CRITERION_NAMES = {
    1: "Unrestricted Intellectual Scope",
    2: "Generative Causal World and Self Model",
    3: "Autonomous Goal Decomposition",
    4: "Self-Directed Learning",
    5: "Epistemological Meta-Reasoning",
}


def _build_claims_document(wave1_outputs: list[dict]) -> str:
    """
    Format all Wave 1 outputs into a single claims document for Wave 2.
    Groups by criterion for readability.
    """
    by_criterion: dict[int, list[str]] = {1: [], 2: [], 3: [], 4: [], 5: []}
    uncategorised: list[str] = []

    for output in wave1_outputs:
        claims = output.get("claims") or []
        source_weight = output.get("source_weight", 3)
        source_name = output.get("source_name", "Unknown")
        weight_just = output.get("weight_justification", "")

        for claim in claims:
            criterion = claim.get("criterion")
            confidence = claim.get("confidence", "medium")
            evidence_type = claim.get("evidence_type", "unknown")
            notes = claim.get("notes", "")
            claim_text = claim.get("claim", "")

            line = (
                f"- [W{source_weight}] [{confidence}] [{evidence_type}] {claim_text}"
                + (f" — {notes}" if notes else "")
                + f" (Source: {source_name})"
            )
            if criterion in by_criterion:
                by_criterion[criterion].append(line)
            else:
                uncategorised.append(line)

    parts = []
    for crit_num, crit_name in CRITERION_NAMES.items():
        lines = by_criterion.get(crit_num, [])
        parts.append(f"### Criterion {crit_num}: {crit_name} ({len(lines)} claims)")
        if lines:
            parts.extend(lines)
        else:
            parts.append("- No claims extracted for this criterion in this cycle.")
        parts.append("")

    if uncategorised:
        parts.append(f"### Uncategorised ({len(uncategorised)} claims)")
        parts.extend(uncategorised)

    return "\n".join(parts)


def _count_sources(wave1_outputs: list[dict]) -> int:
    """Count unique source IDs in the wave1 outputs."""
    return len({o.get("source_id") for o in wave1_outputs if o.get("source_id")})


def run_wave2(provider: LLMProvider, report_cycle_id: str, wave1_summary: dict) -> dict:
    """
    Run Wave 2 synthesis to produce the final report tree JSON.

    Returns a dict with keys: report_tree, scenario_assessment, cost_usd, batch_id.
    """
    wave1_outputs = get_wave1_outputs_for_cycle(report_cycle_id)
    if not wave1_outputs:
        raise ValueError(f"No Wave 1 outputs found for report cycle: {report_cycle_id}")

    claims_document = _build_claims_document(wave1_outputs)
    sources_covered = _count_sources(wave1_outputs)
    now = datetime.now(timezone.utc)
    date_range = f"up to {now.strftime('%Y-%m-%d')}"

    system_prompt = build_wave2_system_prompt()

    if len(claims_document) > MAX_CLAIMS_CHARS:
        logger.info(
            f"Claims document is {len(claims_document):,} chars — splitting Wave 2 by criterion"
        )
        return _run_wave2_split(
            provider=provider,
            report_cycle_id=report_cycle_id,
            wave1_outputs=wave1_outputs,
            system_prompt=system_prompt,
            date_range=date_range,
            total_items=wave1_summary.get("items_processed", 0),
            sources_covered=sources_covered,
        )

    user_prompt = build_wave2_user_prompt(
        report_cycle_id=report_cycle_id,
        date_range=date_range,
        total_items=wave1_summary.get("items_processed", 0),
        sources_covered=sources_covered,
        claims_document=claims_document,
    )

    custom_id = f"w2-main-{str(uuid.uuid4())[:12]}"
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

    logger.info("Submitting Wave 2 batch (single call)")
    batch_id = provider.submit_batch(batch_requests)
    results = provider.wait_for_batch(batch_id, poll_interval_seconds=30)

    result = results[0]
    if result.error:
        raise RuntimeError(f"Wave 2 API call failed: {result.error}")

    try:
        report_tree = json.loads(result.content)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Failed to parse Wave 2 output as JSON: {e}\nContent preview: {result.content[:500]}"
        ) from e

    scenario_assessment = (
        report_tree.get("executive_summary", {}).get("scenario_assessment", "A")
    )

    return {
        "report_tree": report_tree,
        "scenario_assessment": scenario_assessment,
        "cost_usd": result.cost_usd,
        "batch_id": batch_id,
        "tokens_used": result.tokens_input + result.tokens_output,
    }


def _run_wave2_split(
    provider: LLMProvider,
    report_cycle_id: str,
    wave1_outputs: list[dict],
    system_prompt: str,
    date_range: str,
    total_items: int,
    sources_covered: int,
) -> dict:
    """
    Split Wave 2 into one call per criterion + one final synthesis call.
    Used when the claims document exceeds MAX_CLAIMS_CHARS.
    """
    # Build per-criterion claims
    by_criterion: dict[int, list[dict]] = {1: [], 2: [], 3: [], 4: [], 5: []}
    for output in wave1_outputs:
        for claim in output.get("claims") or []:
            c = claim.get("criterion")
            if c in by_criterion:
                by_criterion[c].append({
                    "claim_text": claim.get("claim", ""),
                    "confidence": claim.get("confidence", "medium"),
                    "evidence_type": claim.get("evidence_type", "unknown"),
                    "notes": claim.get("notes", ""),
                    "source_weight": output.get("source_weight", 3),
                    "source_name": output.get("source_name", "Unknown"),
                })

    # Build batch requests for each criterion
    batch_requests: list[BatchRequest] = []
    custom_id_to_criterion: dict[str, int] = {}

    for crit_num, crit_name in CRITERION_NAMES.items():
        claims = by_criterion.get(crit_num, [])
        crit_doc = "\n".join(
            f"- [W{c['source_weight']}] [{c['confidence']}] [{c['evidence_type']}] {c['claim_text']}"
            + (f" — {c['notes']}" if c.get("notes") else "")
            + f" (Source: {c['source_name']})"
            for c in claims
        ) or "- No claims extracted for this criterion."

        custom_id = f"w2-c{crit_num}-{str(uuid.uuid4())[:8]}"
        custom_id_to_criterion[custom_id] = crit_num

        user_prompt = f"""Criterion {crit_num}: {crit_name}

Claims from all sources for this criterion:

{crit_doc}

Produce the criterion JSON branch ONLY (not the full report tree). Schema:
{{
  "id": "c{crit_num}",
  "title": "Criterion {crit_num}: {crit_name}",
  "summary": "<2-3 sentence verdict>",
  "satisfaction_pct": <integer 0-100>,
  "clusters": [
    {{
      "id": "c{crit_num}.N",
      "title": "<cluster title>",
      "summary": "<paragraph>",
      "items": [
        {{
          "id": "c{crit_num}.N.M",
          "title": "<evidence title>",
          "detail": "<detailed evidence with specific numbers>",
          "references": [{{"source": "<name>", "url": "<url>", "date": "<YYYY-MM-DD>", "weight": <1-5>}}]
        }}
      ]
    }}
  ]
}}

Include 3-5 clusters with 2-4 items each."""

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

    logger.info(f"Submitting Wave 2 split batch: {len(batch_requests)} criterion calls")
    batch_id_1 = provider.submit_batch(batch_requests)
    criterion_results = provider.wait_for_batch(batch_id_1, poll_interval_seconds=30)

    criterion_trees: dict[int, dict] = {}
    total_cost = 0.0
    for result in criterion_results:
        crit_num = custom_id_to_criterion.get(result.custom_id)
        total_cost += result.cost_usd
        if result.error:
            logger.error(f"Criterion {crit_num} Wave 2 call failed: {result.error}")
            continue
        try:
            criterion_trees[crit_num] = json.loads(result.content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse criterion {crit_num} result: {e}")

    # Final synthesis call
    synthesis_custom_id = f"w2-synth-{str(uuid.uuid4())[:8]}"
    synthesis_prompt = f"""Given these five criterion branch assessments, produce the complete report tree JSON.

Criterion assessments:
{json.dumps(criterion_trees, indent=2)[:40000]}

Output the full report tree with executive summary and cross-criterion analysis. Follow the schema exactly:
{{
  "executive_summary": {{ "id": "exec", "title": "Executive Summary", "summary": "...", "scenario_assessment": "...", "scenario_rationale": "..." }},
  "criteria": [ ...the five criterion branches, possibly improved from the above... ],
  "cross_criterion_analysis": {{ "id": "cross", "title": "Cross-Criterion Analysis", "summary": "..." }}
}}"""

    synthesis_requests = [
        BatchRequest(
            custom_id=synthesis_custom_id,
            system_prompt=system_prompt,
            user_prompt=synthesis_prompt,
            max_tokens=8192,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
    ]
    logger.info("Submitting Wave 2 synthesis call")
    batch_id_2 = provider.submit_batch(synthesis_requests)
    synthesis_results = provider.wait_for_batch(batch_id_2, poll_interval_seconds=30)

    synthesis_result = synthesis_results[0]
    total_cost += synthesis_result.cost_usd

    if synthesis_result.error:
        raise RuntimeError(f"Wave 2 synthesis call failed: {synthesis_result.error}")

    try:
        report_tree = json.loads(synthesis_result.content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse Wave 2 synthesis output: {e}") from e

    scenario_assessment = (
        report_tree.get("executive_summary", {}).get("scenario_assessment", "A")
    )

    return {
        "report_tree": report_tree,
        "scenario_assessment": scenario_assessment,
        "cost_usd": total_cost,
        "batch_id": f"{batch_id_1},{batch_id_2}",
        "tokens_used": synthesis_result.tokens_input + synthesis_result.tokens_output,
    }
