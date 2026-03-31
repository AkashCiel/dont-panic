"""Write output/index.html landing page with links to cognitive and diffusion reports."""
from __future__ import annotations

import os
import sys
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def write_landing(output_path: Optional[str] = None) -> str:
    out = output_path or os.path.join(ROOT, "output", "index.html")
    cognitive = os.path.join(ROOT, "output", "cognitive", "index.html")
    diffusion = os.path.join(ROOT, "output", "diffusion", "index.html")
    has_cog = os.path.isfile(cognitive)
    has_diff = os.path.isfile(diffusion)

    cog_block = (
        f'<p><a href="cognitive/index.html">AGI Capability Tracker (cognitive)</a> — '
        f"five-criterion research assessment.</p>"
        if has_cog
        else "<p><em>Cognitive report HTML not generated yet.</em></p>"
    )
    diff_block = (
        f'<p><a href="diffusion/index.html">AI Diffusion Tracker</a> — '
        f"societal adoption and disruption analysis.</p>"
        if has_diff
        else "<p><em>Diffusion report HTML not generated yet.</em></p>"
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Trackers — Home</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f8fafc; color: #0f172a; line-height: 1.6; max-width: 640px; margin: 48px auto; padding: 0 16px; }}
h1 {{ font-size: 1.5rem; margin-bottom: 12px; }}
p {{ margin: 12px 0; }}
a {{ color: #2563eb; }}
</style>
</head>
<body>
<h1>AI Capability &amp; Diffusion Reports</h1>
<p>Static reports generated from curated sources and LLM analysis.</p>
{cog_block}
{diff_block}
</body>
</html>"""
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    return out


def main():
    write_landing()
    print(f"Landing page written to: {os.path.join(ROOT, 'output', 'index.html')}")


if __name__ == "__main__":
    main()
