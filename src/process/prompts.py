"""Prompt templates for Wave 1 and Wave 2 LLM calls."""
import os


def get_framework_text() -> str:
    """Read the AGI evaluation framework document from the repository."""
    framework_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "framework",
        "agi_evaluation_framework.md",
    )
    with open(framework_path, "r", encoding="utf-8") as f:
        return f.read()


WAVE1_SYSTEM_PROMPT_TEMPLATE = """\
You are an expert analyst evaluating AI research and news against an AGI evaluation framework.

{framework}

## Source Weight Guidelines

| Weight | Description | Examples |
|--------|-------------|---------|
| 5 | Peer-reviewed benchmark with transparent methodology, independent research org | ARC-AGI results, Epoch AI quantitative data, peer-reviewed papers |
| 4 | Major lab primary publication with reproducible claims | DeepMind blog announcing AlphaProof, OpenAI system cards |
| 3 | Expert analysis by credentialed researcher | Import AI, Interconnects, Zvi's roundup |
| 2 | Institutional assessment or curated leaderboard | UK AISI report, HuggingFace leaderboard, SWE-bench |
| 1 | Community discussion or unverified claims | LessWrong posts, trending repos |

## Your Task

Analyze the provided content from a specific AI information source. Extract all claims relevant to AGI progress, map each claim to one of the five AGI criteria (1–5), and assign a source weight (1–5).

Output ONLY valid JSON matching this schema exactly:
{{
  "source_id": <integer>,
  "source_name": "<string>",
  "source_weight": <1-5>,
  "weight_justification": "<one sentence explaining the weight>",
  "claims": [
    {{
      "claim": "<specific factual claim, as precise as possible>",
      "criterion": <1|2|3|4|5>,
      "evidence_type": "<benchmark_score|lab_announcement|research_finding|community_discussion|quantitative_data|expert_analysis>",
      "confidence": "<high|medium|low>",
      "notes": "<optional: caveats, context, or why confidence is as assessed>"
    }}
  ]
}}

Rules:
- Map each claim to the single most relevant AGI criterion.
- If no content is relevant to any AGI criterion, return an empty claims array.
- Do not fabricate claims — only extract what the content explicitly states or strongly implies.
- Be specific: prefer "GPT-5 achieves 87.4% on MMLU" over "GPT-5 performs well on benchmarks".
"""

WAVE1_USER_PROMPT_TEMPLATE = """\
Source: {source_name} (ID: {source_id}, Category: {category})
Default weight: {weight_default}

Content items to analyze:

{content}

Extract all claims relevant to AGI progress from the above content. Map each claim to one of the five AGI criteria."""

WAVE2_SYSTEM_PROMPT_TEMPLATE = """\
You are an expert analyst synthesizing evidence about AGI progress from multiple sources.

{framework}

## Your Task

You are given a collection of weighted claims extracted from multiple AI research sources. Synthesize these into a structured report tree assessing where current AI systems stand relative to AGI.

Output ONLY valid JSON matching this report tree schema exactly:
{{
  "executive_summary": {{
    "id": "exec",
    "title": "Executive Summary",
    "summary": "<3-4 sentence overall assessment of the current state of AGI progress>",
    "scenario_assessment": "<one of: A, A→B, B, B→C, C, C→D, D, D→E, E>",
    "scenario_rationale": "<2-3 sentences explaining the scenario choice with specific evidence>"
  }},
  "criteria": [
    {{
      "id": "c1",
      "title": "Criterion 1: Unrestricted Intellectual Scope",
      "summary": "<2-3 sentence verdict for this criterion>",
      "satisfaction_pct": <integer 0-100>,
      "clusters": [
        {{
          "id": "c1.1",
          "title": "<evidence cluster title>",
          "summary": "<paragraph-length evidence cluster summary>",
          "items": [
            {{
              "id": "c1.1.1",
              "title": "<specific evidence title>",
              "detail": "<detailed evidence with specific numbers and citations>",
              "references": [
                {{"source": "<source name>", "url": "<url or empty string>", "date": "<YYYY-MM-DD or empty>", "weight": <1-5>}}
              ]
            }}
          ]
        }}
      ]
    }}
  ],
  "cross_criterion_analysis": {{
    "id": "cross",
    "title": "Cross-Criterion Analysis",
    "summary": "<paragraph discussing interdependencies between criteria and what the overall pattern reveals about AGI timelines>"
  }}
}}

## Scenario Definitions
- A: Current state — weak/no progress on all five criteria. Statistical engines that mimic reasoning without genuine causal understanding.
- B: Superhuman Domain Tool — strong Criterion 1, weak C2, weak C3, no C4, no C5. Superhuman on specific tasks but still a tool requiring human direction.
- C: Autonomous Digital Agent — strong C1, weak C2, strong C3, no C4, no C5. Can pursue extended goals without re-prompting; still statistically bounded.
- D: Bootstrapped AGI — strong C1-C3, partial C4, partial C5. Beginning of genuine self-directed learning and epistemological meta-reasoning.
- E: Full AGI — all five criteria fully satisfied simultaneously.

## Evaluation Standards
- Be rigorous. Distinguish genuine progress from superficial progress per the framework definitions.
- Benchmark scores alone do not satisfy criteria — assess whether they reflect genuine architectural capability.
- Each criterion should have 3-5 evidence clusters, each cluster with 2-4 specific evidence items.
- Cite specific numbers and source names in evidence items.
"""

WAVE2_USER_PROMPT_TEMPLATE = """\
Report cycle: {report_cycle_id}
Period: {date_range}
Total items analyzed: {total_items}
Sources covered: {sources_covered}

## Weighted Claims from All Sources

{claims_document}

Synthesize the above weighted claims into the full report tree JSON."""


def build_wave1_system_prompt() -> str:
    """Build the Wave 1 system prompt with the full framework embedded."""
    framework = get_framework_text()
    return WAVE1_SYSTEM_PROMPT_TEMPLATE.format(framework=framework)


def build_wave1_user_prompt(
    source_id: int,
    source_name: str,
    category: str,
    weight_default: int,
    items: list[dict],
) -> str:
    """Build the Wave 1 user prompt for a batch of items from one source."""
    content_parts = []
    for i, item in enumerate(items, 1):
        published = item.get("published_at", "")
        if hasattr(published, "strftime"):
            published = published.strftime("%Y-%m-%d")
        content_raw = str(item.get("content", ""))[:2000]
        part = (
            f"[Item {i}]\n"
            f"Title: {item.get('title', 'N/A')}\n"
            f"URL: {item.get('url', 'N/A')}\n"
            f"Date: {published}\n"
            f"Content: {content_raw}"
        )
        content_parts.append(part)

    content = "\n\n---\n\n".join(content_parts)
    return WAVE1_USER_PROMPT_TEMPLATE.format(
        source_name=source_name,
        source_id=source_id,
        category=category,
        weight_default=weight_default,
        content=content,
    )


def build_wave2_system_prompt() -> str:
    """Build the Wave 2 system prompt with the full framework embedded."""
    framework = get_framework_text()
    return WAVE2_SYSTEM_PROMPT_TEMPLATE.format(framework=framework)


def build_wave2_user_prompt(
    report_cycle_id: str,
    date_range: str,
    total_items: int,
    sources_covered: int,
    claims_document: str,
) -> str:
    """Build the Wave 2 user prompt from the aggregated claims document."""
    return WAVE2_USER_PROMPT_TEMPLATE.format(
        report_cycle_id=report_cycle_id,
        date_range=date_range,
        total_items=total_items,
        sources_covered=sources_covered,
        claims_document=claims_document,
    )
