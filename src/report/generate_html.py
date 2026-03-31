"""
Generate a self-contained static HTML report from the report tree JSON.

Usage:
    python src/report/generate_html.py [--report-json PATH] [--output PATH]

Reads:  output/latest_report.json
Writes: output/cognitive/index.html (landing page: output/index.html via generate_landing.py)
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCENARIO_COLORS = {
    "A": ("#dc2626", "#fee2e2"),    # red
    "A→B": ("#ea580c", "#ffedd5"),  # orange-red
    "B": ("#d97706", "#fef3c7"),    # amber
    "B→C": ("#ca8a04", "#fefce8"),  # yellow
    "C": ("#65a30d", "#f7fee7"),    # lime
    "C→D": ("#16a34a", "#dcfce7"),  # green
    "D": ("#0d9488", "#ccfbf1"),    # teal
    "D→E": ("#0891b2", "#e0f2fe"),  # cyan
    "E": ("#7c3aed", "#ede9fe"),    # violet
}

SCENARIO_LABELS = {
    "A": "Scenario A — Current State",
    "A→B": "Transitioning A→B",
    "B": "Scenario B — Superhuman Domain Tool",
    "B→C": "Transitioning B→C",
    "C": "Scenario C — Autonomous Digital Agent",
    "C→D": "Transitioning C→D",
    "D": "Scenario D — Bootstrapped AGI",
    "D→E": "Transitioning D→E",
    "E": "Scenario E — Full AGI",
}

INLINE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; color: #1e293b; line-height: 1.6; }
.container { max-width: 900px; margin: 0 auto; padding: 24px 16px 80px; }
header { background: #0f172a; color: #f8fafc; padding: 32px 24px; text-align: center; margin-bottom: 32px; border-radius: 8px; }
header h1 { font-size: 1.8rem; font-weight: 700; margin-bottom: 8px; }
header p { color: #94a3b8; font-size: 0.9rem; }
.scenario-badge { display: inline-block; padding: 10px 24px; border-radius: 6px; font-size: 1.1rem; font-weight: 700; margin: 16px 0; }
.exec-summary { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px; margin-bottom: 24px; }
.exec-summary h2 { font-size: 1.2rem; color: #0f172a; margin-bottom: 12px; }
.exec-summary .summary-text { color: #475569; }
.exec-summary .rationale { margin-top: 12px; font-size: 0.9rem; color: #64748b; font-style: italic; border-left: 3px solid #e2e8f0; padding-left: 12px; }
.criterion { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 16px; overflow: hidden; }
.criterion-header { padding: 20px 24px; cursor: pointer; display: flex; align-items: center; justify-content: space-between; user-select: none; transition: background 0.15s; }
.criterion-header:hover { background: #f1f5f9; }
.criterion-title-group { flex: 1; }
.criterion-title { font-size: 1.05rem; font-weight: 600; color: #0f172a; }
.criterion-summary { font-size: 0.85rem; color: #64748b; margin-top: 4px; }
.criterion-meta { display: flex; align-items: center; gap: 16px; flex-shrink: 0; margin-left: 16px; }
.satisfaction { text-align: right; }
.satisfaction-pct { font-size: 1.1rem; font-weight: 700; color: #0f172a; }
.satisfaction-bar { width: 80px; height: 6px; background: #e2e8f0; border-radius: 3px; margin-top: 4px; overflow: hidden; }
.satisfaction-fill { height: 100%; border-radius: 3px; background: linear-gradient(90deg, #ef4444, #f59e0b, #22c55e); }
.chevron { color: #94a3b8; font-size: 1.2rem; transition: transform 0.2s; }
.criterion-header.open .chevron { transform: rotate(180deg); }
.clusters { display: none; padding: 0 24px 20px; border-top: 1px solid #f1f5f9; }
.clusters.open { display: block; }
.cluster { margin-top: 16px; }
.cluster-header { padding: 12px 16px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }
.cluster-header:hover { background: #f1f5f9; }
.cluster-title { font-size: 0.95rem; font-weight: 600; color: #334155; }
.cluster-summary { font-size: 0.85rem; color: #64748b; margin-top: 4px; }
.cluster-chevron { color: #94a3b8; font-size: 1rem; transition: transform 0.2s; }
.cluster-header.open .cluster-chevron { transform: rotate(180deg); }
.cluster-items { display: none; margin-top: 8px; padding-left: 16px; }
.cluster-items.open { display: block; }
.evidence-item { background: #fff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px 16px; margin-top: 8px; }
.evidence-title { font-size: 0.9rem; font-weight: 600; color: #1e293b; margin-bottom: 6px; }
.evidence-detail { font-size: 0.85rem; color: #475569; }
.evidence-refs { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 6px; }
.ref-tag { font-size: 0.75rem; background: #f1f5f9; border: 1px solid #e2e8f0; color: #64748b; padding: 2px 8px; border-radius: 12px; }
.ref-tag a { color: inherit; text-decoration: none; }
.ref-tag a:hover { color: #3b82f6; }
.cross-criterion { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px; margin-top: 24px; }
.cross-criterion h2 { font-size: 1.1rem; font-weight: 600; margin-bottom: 12px; }
.cross-criterion p { color: #475569; font-size: 0.9rem; }
.methodology { margin-top: 40px; padding: 24px; background: #f1f5f9; border-radius: 8px; font-size: 0.85rem; color: #64748b; }
.methodology h3 { font-size: 0.95rem; font-weight: 600; color: #334155; margin-bottom: 8px; }
.sources-footer { margin-top: 24px; font-size: 0.8rem; color: #94a3b8; }
.label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; font-weight: 600; margin-bottom: 4px; }
@media (max-width: 600px) {
    .criterion-meta { display: none; }
    .criterion-header { flex-wrap: wrap; }
    header h1 { font-size: 1.4rem; }
}
"""

INLINE_JS = """
function toggle(headerId, contentId) {
    const header = document.getElementById(headerId);
    const content = document.getElementById(contentId);
    const isOpen = content.classList.contains('open');
    content.classList.toggle('open', !isOpen);
    header.classList.toggle('open', !isOpen);
}
</script>
"""


def _esc(text: str) -> str:
    """HTML-escape a string."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _pct_color(pct: int) -> str:
    """Return a color based on satisfaction percentage."""
    if pct >= 70:
        return "#22c55e"
    if pct >= 40:
        return "#f59e0b"
    return "#ef4444"


def render_references(references: list[dict]) -> str:
    if not references:
        return ""
    tags = []
    for ref in references:
        source = _esc(ref.get("source", ""))
        url = ref.get("url", "")
        date = _esc(ref.get("date", ""))
        weight = ref.get("weight", "")
        label = f"W{weight} · {source}" + (f" · {date}" if date else "")
        if url and url.startswith("http"):
            tags.append(f'<span class="ref-tag"><a href="{_esc(url)}" target="_blank">{label}</a></span>')
        else:
            tags.append(f'<span class="ref-tag">{label}</span>')
    return f'<div class="evidence-refs">{"".join(tags)}</div>'


def render_item(item: dict, item_idx: int) -> str:
    title = _esc(item.get("title", "Evidence"))
    detail = _esc(item.get("detail", ""))
    refs_html = render_references(item.get("references", []))
    return f"""
<div class="evidence-item">
    <div class="evidence-title">{title}</div>
    <div class="evidence-detail">{detail}</div>
    {refs_html}
</div>"""


def render_cluster(cluster: dict, crit_idx: int, cluster_idx: int) -> str:
    header_id = f"ch-{crit_idx}-{cluster_idx}"
    items_id = f"ci-{crit_idx}-{cluster_idx}"
    title = _esc(cluster.get("title", "Evidence Cluster"))
    summary = _esc(cluster.get("summary", ""))

    items_html = "".join(
        render_item(item, i) for i, item in enumerate(cluster.get("items", []))
    )

    return f"""
<div class="cluster">
    <div class="cluster-header" id="{header_id}" onclick="toggle('{header_id}', '{items_id}')" role="button" tabindex="0">
        <div>
            <div class="cluster-title">{title}</div>
            <div class="cluster-summary">{summary}</div>
        </div>
        <span class="cluster-chevron">▾</span>
    </div>
    <div class="cluster-items" id="{items_id}">
        {items_html}
    </div>
</div>"""


def render_criterion(criterion: dict, crit_idx: int) -> str:
    header_id = f"crh-{crit_idx}"
    body_id = f"crb-{crit_idx}"
    title = _esc(criterion.get("title", f"Criterion {crit_idx + 1}"))
    summary = _esc(criterion.get("summary", ""))
    pct = int(criterion.get("satisfaction_pct", 0))
    color = _pct_color(pct)

    clusters_html = "".join(
        render_cluster(cluster, crit_idx, i)
        for i, cluster in enumerate(criterion.get("clusters", []))
    )

    return f"""
<div class="criterion">
    <div class="criterion-header" id="{header_id}" onclick="toggle('{header_id}', '{body_id}')" role="button" tabindex="0">
        <div class="criterion-title-group">
            <div class="criterion-title">{title}</div>
            <div class="criterion-summary">{summary}</div>
        </div>
        <div class="criterion-meta">
            <div class="satisfaction">
                <div class="satisfaction-pct" style="color:{color}">{pct}%</div>
                <div class="satisfaction-bar">
                    <div class="satisfaction-fill" style="width:{pct}%;background:{color}"></div>
                </div>
            </div>
            <span class="chevron">▾</span>
        </div>
    </div>
    <div class="clusters" id="{body_id}">
        {clusters_html}
    </div>
</div>"""


def render_report(report_tree: dict, metadata: dict) -> str:
    """Render the full HTML page from report_tree and metadata."""
    exec_sum = report_tree.get("executive_summary", {})
    scenario = metadata.get("scenario_assessment", exec_sum.get("scenario_assessment", "A"))
    scenario_color, scenario_bg = SCENARIO_COLORS.get(scenario, ("#6b7280", "#f3f4f6"))
    scenario_label = SCENARIO_LABELS.get(scenario, f"Scenario {scenario}")

    exec_summary_text = _esc(exec_sum.get("summary", ""))
    exec_rationale = _esc(exec_sum.get("scenario_rationale", ""))

    criteria_html = "".join(
        render_criterion(criterion, i)
        for i, criterion in enumerate(report_tree.get("criteria", []))
    )

    cross = report_tree.get("cross_criterion_analysis", {})
    cross_summary = _esc(cross.get("summary", ""))

    created_at = metadata.get("created_at", "")
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            created_at = dt.strftime("%Y-%m-%d %H:%M UTC")
        except Exception:
            pass

    report_id = _esc(metadata.get("report_cycle_id", ""))
    total_cost = metadata.get("total_cost_usd", 0)
    items = metadata.get("items_analysed", 0)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AGI Capability Tracker — Report</title>
<style>{INLINE_CSS}</style>
</head>
<body>
<div class="container">

<header>
    <h1>AGI Capability Tracker</h1>
    <p>Automated analysis of AI research against a five-criterion AGI evaluation framework</p>
    <div class="scenario-badge" style="background:{scenario_bg};color:{scenario_color}">
        {_esc(scenario_label)}
    </div>
    <p style="margin-top:8px;font-size:0.8rem;color:#94a3b8">
        Generated: {_esc(created_at)} · {items} items analysed · ${total_cost:.4f} API cost
    </p>
    <p style="margin-top:10px;font-size:0.85rem"><a href="../index.html" style="color:#93c5fd">Home</a> ·
    <a href="../diffusion/index.html" style="color:#93c5fd">AI Diffusion report →</a></p>
</header>

<div class="exec-summary">
    <div class="label">Executive Summary</div>
    <div class="summary-text">{exec_summary_text}</div>
    {f'<div class="rationale">{exec_rationale}</div>' if exec_rationale else ''}
</div>

{criteria_html}

<div class="cross-criterion">
    <h2>Cross-Criterion Analysis</h2>
    <p>{cross_summary}</p>
</div>

<div class="methodology">
    <h3>Methodology</h3>
    <p>This report is generated automatically every 3 days by fetching content from 20 curated AI research sources,
    then running a two-wave LLM analysis pipeline against the five-criterion AGI evaluation framework.
    <strong>Wave 1</strong> extracts and weights specific claims from each source.
    <strong>Wave 2</strong> synthesises all weighted claims into this report tree.</p>
    <p style="margin-top:8px">The five AGI criteria assessed are:
    (1) Unrestricted Intellectual Scope,
    (2) Generative Causal World and Self Model,
    (3) Autonomous Goal Decomposition,
    (4) Self-Directed Learning,
    (5) Epistemological Meta-Reasoning.
    AGI requires all five criteria to be satisfied simultaneously.</p>
    <p style="margin-top:8px;font-size:0.8rem">Report ID: {report_id} · Model: gpt-4o via Batch API</p>
</div>

</div>
<script>
{INLINE_JS}
</script>
</body>
</html>"""


def load_report(path: str) -> dict:
    """Load and return the report JSON from file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Generate HTML report from report JSON")
    parser.add_argument("--report-json", default=os.path.join(ROOT, "output", "latest_report.json"))
    parser.add_argument("--output", default=os.path.join(ROOT, "output", "cognitive", "index.html"))
    args = parser.parse_args()

    if not os.path.exists(args.report_json):
        print(f"Report JSON not found: {args.report_json}", file=sys.stderr)
        sys.exit(1)

    data = load_report(args.report_json)
    report_tree = data.get("report_tree", {})
    metadata = {
        "report_cycle_id": data.get("report_cycle_id", ""),
        "created_at": data.get("created_at", ""),
        "scenario_assessment": data.get("scenario_assessment", "A"),
        "total_cost_usd": data.get("total_cost_usd", 0),
        "items_analysed": data.get("items_analysed", 0),
    }

    html = render_report(report_tree, metadata)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"HTML report written to: {args.output}")


if __name__ == "__main__":
    main()
