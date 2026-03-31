"""
Generate static HTML for the diffusion report tree.

Reads:  output/latest_diffusion_report.json
Writes: output/diffusion/index.html
"""
import argparse
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

INLINE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f0fdf4; color: #14532d; line-height: 1.6; }
.container { max-width: 920px; margin: 0 auto; padding: 24px 16px 80px; }
header { background: #14532d; color: #ecfdf5; padding: 28px 24px; text-align: center; margin-bottom: 28px; border-radius: 8px; }
header h1 { font-size: 1.75rem; font-weight: 700; margin-bottom: 8px; }
header p { color: #bbf7d0; font-size: 0.9rem; }
a.nav { color: #86efac; }
.node { background: #fff; border: 1px solid #bbf7d0; border-radius: 8px; margin-bottom: 12px; overflow: hidden; }
.node-header { padding: 16px 18px; cursor: pointer; display: flex; justify-content: space-between; align-items: flex-start; user-select: none; }
.node-header:hover { background: #f0fdf4; }
.node-title { font-weight: 600; color: #14532d; font-size: 1rem; }
.node-summary { font-size: 0.88rem; color: #166534; margin-top: 6px; }
.chevron { color: #22c55e; font-size: 1.1rem; flex-shrink: 0; margin-left: 12px; transition: transform 0.2s; }
.node-header.open .chevron { transform: rotate(180deg); }
.children { display: none; padding: 0 12px 14px 24px; border-top: 1px solid #ecfdf5; }
.children.open { display: block; }
.three-q { background: #ecfdf5; border-radius: 8px; padding: 16px 18px; margin-top: 20px; border: 1px solid #bbf7d0; }
.three-q h2 { font-size: 1.05rem; margin-bottom: 10px; color: #14532d; }
.three-q p { margin-bottom: 8px; font-size: 0.92rem; }
footer { margin-top: 32px; font-size: 0.8rem; color: #6b7280; }
"""

INLINE_JS = """
function toggle(id) {
  var el = document.getElementById(id);
  if (!el) return;
  el.classList.toggle('open');
  var h = document.getElementById('h-'+id);
  if (h) h.classList.toggle('open');
}
"""


def _esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def _render_children(children: list, prefix: str, depth: int) -> str:
    if not children:
        return ""
    parts = []
    for i, ch in enumerate(children):
        if not isinstance(ch, dict):
            continue
        cid = ch.get("id") or f"{prefix}-{depth}-{i}"
        cid_safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(cid))[:80]
        uid = f"n-{prefix}-{cid_safe}-{depth}-{i}"
        title = _esc(ch.get("title", ""))
        summary = _esc(ch.get("summary", ""))
        sub = ch.get("children") or []
        sub_html = _render_children(sub, uid, depth + 1)
        parts.append(f"""
<div class="node">
  <div class="node-header" id="h-{uid}" onclick="toggle('{uid}')" role="button" tabindex="0">
    <div>
      <div class="node-title">{title}</div>
      <div class="node-summary">{summary}</div>
    </div>
    <span class="chevron">▾</span>
  </div>
  <div class="children" id="{uid}">{sub_html}</div>
</div>""")
    return "\n".join(parts)


def render_diffusion_report(report_tree: dict, metadata: dict) -> str:
    exec_sum = report_tree.get("executive_summary") or {}
    exec_title = _esc(exec_sum.get("title", "Executive Summary"))
    exec_text = _esc(exec_sum.get("summary", ""))

    sections = report_tree.get("sections") or []
    sections_html = _render_children(sections, "sec", 0)

    tq = report_tree.get("three_questions") or {}
    supply = report_tree.get("supply_constraints") or {}

    supply_html = ""
    if supply:
        supply_html = f"""
<div class="node" style="margin-top:16px">
  <div class="node-header open" id="h-supply" onclick="toggle('supply-box')" role="button">
    <div>
      <div class="node-title">{_esc(supply.get('title', 'Supply constraints'))}</div>
      <div class="node-summary">{_esc(supply.get('summary', ''))}</div>
    </div>
    <span class="chevron">▾</span>
  </div>
  <div class="children open" id="supply-box">{_render_children(supply.get('children') or [], 'sup', 1)}</div>
</div>"""

    three_q_html = ""
    if tq:
        three_q_html = f"""
<div class="three-q">
  <h2>Three questions</h2>
  <p><strong>Q1 (today):</strong> {_esc(tq.get('q1_today', ''))}</p>
  <p><strong>Q2 (near future):</strong> {_esc(tq.get('q2_near_future', ''))}</p>
  <p><strong>Q3 (industry absorption):</strong> {_esc(tq.get('q3_industry_absorption', ''))}</p>
</div>"""

    created = metadata.get("created_at", "")
    report_id = _esc(metadata.get("report_cycle_id", ""))
    total_cost = metadata.get("total_cost_usd", 0)
    items = metadata.get("items_analysed", 0)
    sources = metadata.get("sources_covered", 0)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Diffusion Tracker — Report</title>
<style>{INLINE_CSS}</style>
</head>
<body>
<div class="container">
<header>
  <h1>AI Diffusion Tracker</h1>
  <p>How AI capabilities propagate through society — adoption, institutions, and downstream effects</p>
  <p style="margin-top:10px"><a class="nav" href="../cognitive/index.html">Cognitive capability report →</a> ·
  <a class="nav" href="../index.html">Home</a></p>
  <p style="margin-top:8px;font-size:0.8rem;color:#bbf7d0">
    Generated: {_esc(created)} · {items} items · {sources} sources · ${total_cost:.4f} API cost
  </p>
</header>

<div class="node">
  <div class="node-header open" id="h-exec" onclick="toggle('exec-box')" role="button">
    <div>
      <div class="node-title">{exec_title}</div>
      <div class="node-summary">{exec_text}</div>
    </div>
    <span class="chevron">▾</span>
  </div>
  <div class="children" id="exec-box"></div>
</div>

{sections_html}

{three_q_html}

{supply_html}

<footer>Report ID: {report_id} · Diffusion track · Model output via Batch API</footer>
</div>
<script>
{INLINE_JS}
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Generate diffusion HTML from JSON")
    parser.add_argument(
        "--report-json",
        default=os.path.join(ROOT, "output", "latest_diffusion_report.json"),
    )
    parser.add_argument(
        "--output",
        default=os.path.join(ROOT, "output", "diffusion", "index.html"),
    )
    args = parser.parse_args()

    if not os.path.exists(args.report_json):
        print(f"Diffusion report JSON not found: {args.report_json}", file=sys.stderr)
        sys.exit(1)

    with open(args.report_json, encoding="utf-8") as f:
        data = json.load(f)

    report_tree = data.get("report_tree") or {}
    metadata = {
        "report_cycle_id": data.get("report_cycle_id", ""),
        "created_at": data.get("created_at", ""),
        "total_cost_usd": data.get("total_cost_usd", 0),
        "items_analysed": data.get("items_analysed", 0),
        "sources_covered": data.get("sources_covered", 0),
    }

    html_out = render_diffusion_report(report_tree, metadata)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"Diffusion HTML written to: {args.output}")


if __name__ == "__main__":
    main()
