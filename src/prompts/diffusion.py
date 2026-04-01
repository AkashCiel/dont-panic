"""Diffusion track prompt builders (framework: framework/ai_diffusion_framework.md)."""
import json
import os
from typing import Any, Optional

from src.prompts.integrity import apply_context_integrity

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRAMEWORK_PATH = os.path.join(ROOT, "framework", "ai_diffusion_framework.md")


def get_diffusion_framework_text() -> str:
    with open(FRAMEWORK_PATH, encoding="utf-8") as f:
        return f.read()


def build_diffusion_wave1_system_prompt() -> str:
    fw = get_diffusion_framework_text()
    core = f"""You are running Wave 1 of the AI Diffusion Tracker. Follow the framework below exactly.

{fw}

## Output contract

Follow the mandatory response envelope in the system instructions. When context is sufficient, set missing_context to false and put ONLY the following inside "payload":
{{
  "source_id": <int>,
  "source_name": "<string>",
  "source_weight": <1-5>,
  "weight_justification": "<string>",
  "findings": [
    {{
      "finding": "<string>",
      "cascade_order": <0-3>,
      "cascade_category": "<one of: lab_strategy, government_action, cloud_infrastructure, platform_decision, capital_flow, enterprise_adoption, defense_procurement, direct_to_individual, workforce_impact, consumer_impact, supply_constraint, feedback_loop>",
      "player_or_domain": "<string>",
      "evidence_type": "<string>",
      "confidence": "high|medium|low",
      "q1_q2_q3_relevance": "<e.g. Q1, Q2, Q3, Q1,Q2>",
      "notes": "<optional string>"
    }}
  ]
}}

Alternatively, if required context is missing per the framework, use missing_context: true with payload null.
"""
    return apply_context_integrity(core)


def build_diffusion_wave1_user_prompt(
    source_id: int,
    source_name: str,
    category: str,
    weight_default: int,
    items: list[dict],
) -> str:
    lines = [
        f"Source ID: {source_id}",
        f"Source name: {source_name}",
        f"Category: {category}",
        f"Default weight hint: {weight_default} (you may override with justification).",
        "",
        "Analyse the following fetched items together. Extract diffusion-relevant findings only.",
        "",
    ]
    for i, item in enumerate(items, 1):
        lines.append(f"--- Item {i} (id={item.get('id')}) ---")
        lines.append(f"Title: {item.get('title', '')}")
        lines.append(f"URL: {item.get('url', '')}")
        pub = item.get("published_at")
        lines.append(f"Published: {pub}")
        lines.append(f"Content:\n{item.get('content', '')[:12000]}")
        lines.append("")
    lines.append("Output the mandatory JSON envelope with the task result inside \"payload\".")
    return "\n".join(lines)


def format_cognitive_context_block(cognitive_row: Optional[dict]) -> str:
    """Build the labelled cognitive context section for Wave 2 (SPEC section 4)."""
    if not cognitive_row:
        return (
            "--- COGNITIVE TRACK CONTEXT ---\n"
            "No cognitive report is available in the database yet.\n"
            "--- END COGNITIVE TRACK CONTEXT ---"
        )
    tree = cognitive_row.get("report_tree")
    if isinstance(tree, str):
        try:
            tree = json.loads(tree)
        except json.JSONDecodeError:
            tree = {}
    if not isinstance(tree, dict):
        tree = {}
    exec_sum = tree.get("executive_summary") or {}
    scenario = cognitive_row.get("scenario_assessment") or exec_sum.get("scenario_assessment", "")
    created = cognitive_row.get("created_at", "")
    if hasattr(created, "isoformat"):
        created = created.isoformat()
    summary_text = exec_sum.get("summary", "")
    criteria = tree.get("criteria") or []
    lines = [
        f"--- COGNITIVE TRACK CONTEXT (from latest cognitive report, dated {created}) ---",
        f"Scenario Assessment: {scenario}",
    ]
    labels = [
        "Intellectual Scope",
        "Causal World Model",
        "Goal Decomposition",
        "Self-Directed Learning",
        "Meta-Reasoning",
    ]
    for i, c in enumerate(criteria[:5]):
        pct = c.get("satisfaction_pct", "")
        lab = labels[i] if i < len(labels) else c.get("title", "")
        lines.append(f"Criterion {i + 1} ({lab}): {pct}%")
    lines.append(f"Executive Summary: {summary_text}")
    lines.append("--- END COGNITIVE TRACK CONTEXT ---")
    return "\n".join(lines)


def build_diffusion_wave2_system_prompt() -> str:
    fw = get_diffusion_framework_text()
    core = f"""You are running Wave 2 synthesis for the AI Diffusion Tracker. Follow the framework below.

{fw}

## Wave 2 instructions

Aggregate Wave 1 findings into one coherent diffusion report tree. Use the cognitive context block in the user message when present; if it is absent or explicitly states no report is available, follow the MISSING CONTEXT rules for Q2 and scenario-dependent claims.

Follow the mandatory response envelope. When missing_context is false, put the full diffusion report structure inside "payload" using the schema in the user message.
"""
    return apply_context_integrity(core)


def build_diffusion_wave2_user_prompt(
    report_cycle_id: str,
    date_range: str,
    total_items: int,
    sources_covered: int,
    cognitive_context_block: str,
    findings_document: str,
) -> str:
    return f"""Report cycle: {report_cycle_id}
Date range: {date_range}
Items analysed (Wave 1): {total_items}
Distinct sources covered: {sources_covered}

{cognitive_context_block}

## Wave 1 findings (aggregated)

{findings_document}

---

Output the mandatory JSON envelope. When missing_context is false, "payload" must contain:
{{
  "executive_summary": {{
    "id": "exec",
    "title": "Executive Summary",
    "summary": "<3-4 sentences on diffusion state and disruptions>",
    "children": []
  }},
  "sections": [
    {{
      "id": "unique_id",
      "title": "<Layer-1 section title from the diffusion framework (e.g. First-Order Player Moves)>",
      "summary": "<2-3 sentence verdict>",
      "children": [
        {{
          "id": "child_id",
          "title": "<evidence cluster>",
          "summary": "<paragraph>",
          "children": [
            {{
              "id": "leaf_id",
              "title": "<specific evidence>",
              "summary": "<detail with references to sources/items where possible>",
              "children": []
            }}
          ]
        }}
      ]
    }}
  ],
  "three_questions": {{
    "q1_today": "<short answer>",
    "q2_near_future": "<short answer; tie to cognitive scenario if context present>",
    "q3_industry_absorption": "<short answer>"
  }},
  "supply_constraints": {{
    "id": "supply",
    "title": "Supply-Side Constraints and Feedback Loops",
    "summary": "<paragraph>",
    "children": []
  }}
}}

Include 7 Layer-1 themes from the framework — you may combine or split using nested sections as long as coverage is complete."""


def build_diffusion_wave2_partial_prompt(
    cascade_label: str,
    findings_subset: str,
    cognitive_context_block: str,
) -> str:
    return f"""{cognitive_context_block}

## Findings subset ({cascade_label})

{findings_subset}

Output the mandatory JSON envelope. When missing_context is false, "payload" must be:
{{
  "cascade_label": "{cascade_label}",
  "assessment": "<structured notes referencing findings>",
  "key_points": ["<bullet>", "..."]
}}"""


def build_diffusion_wave2_merge_prompt(
    partial_json_docs: list[dict[str, Any]],
    cognitive_context_block: str,
    meta: dict[str, Any],
) -> str:
    return f"""{cognitive_context_block}

Intermediate cascade assessments:
{json.dumps(partial_json_docs, indent=2)[:60000]}

Meta: {json.dumps(meta)}

Merge into the final diffusion report tree (same schema as the single-call Wave 2 user prompt). Output the mandatory JSON envelope with the full report in "payload"."""


__all__ = [
    "build_diffusion_wave1_system_prompt",
    "build_diffusion_wave1_user_prompt",
    "build_diffusion_wave2_system_prompt",
    "build_diffusion_wave2_user_prompt",
    "build_diffusion_wave2_partial_prompt",
    "build_diffusion_wave2_merge_prompt",
    "format_cognitive_context_block",
    "get_diffusion_framework_text",
]
