"""Tests for HTML report generation."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _make_report_tree(scenario="B", n_criteria=5):
    """Build a minimal valid report tree for testing."""
    criteria = []
    for i in range(1, n_criteria + 1):
        criteria.append({
            "id": f"c{i}",
            "title": f"Criterion {i}: Test Criterion",
            "summary": f"Summary for criterion {i}.",
            "satisfaction_pct": i * 15,
            "clusters": [
                {
                    "id": f"c{i}.1",
                    "title": f"Cluster {i}.1",
                    "summary": f"Cluster summary {i}.1.",
                    "items": [
                        {
                            "id": f"c{i}.1.1",
                            "title": f"Evidence item {i}.1.1",
                            "detail": f"Detail with numbers: {i * 10}% improvement.",
                            "references": [
                                {"source": "Test Source", "url": "https://example.com", "date": "2025-01-01", "weight": 3}
                            ],
                        }
                    ],
                }
            ],
        })

    return {
        "executive_summary": {
            "id": "exec",
            "title": "Executive Summary",
            "summary": "Test executive summary.",
            "scenario_assessment": scenario,
            "scenario_rationale": "Test rationale.",
        },
        "criteria": criteria,
        "cross_criterion_analysis": {
            "id": "cross",
            "title": "Cross-Criterion Analysis",
            "summary": "Cross-criterion analysis summary.",
        },
    }


def _make_metadata(scenario="B"):
    return {
        "report_cycle_id": "test-001",
        "created_at": "2025-01-15T08:00:00Z",
        "scenario_assessment": scenario,
        "total_cost_usd": 0.42,
        "items_analysed": 200,
    }


def test_render_report_is_valid_html():
    """render_report produces a string starting with DOCTYPE."""
    from src.report.generate_html import render_report
    html = render_report(_make_report_tree(), _make_metadata())
    assert html.strip().startswith("<!DOCTYPE html>")
    assert "</html>" in html


def test_render_report_includes_all_five_criteria():
    """render_report includes all five criteria titles."""
    from src.report.generate_html import render_report
    html = render_report(_make_report_tree(), _make_metadata())
    for i in range(1, 6):
        assert f"Criterion {i}" in html, f"Missing Criterion {i} in HTML"


def test_render_report_includes_cross_criterion():
    """render_report includes the cross-criterion analysis section."""
    from src.report.generate_html import render_report
    html = render_report(_make_report_tree(), _make_metadata())
    assert "Cross-Criterion Analysis" in html


def test_render_report_includes_executive_summary():
    """render_report includes executive summary content."""
    from src.report.generate_html import render_report
    html = render_report(_make_report_tree(), _make_metadata())
    assert "Executive Summary" in html
    assert "Test executive summary." in html


def test_render_report_scenario_badge_present():
    """render_report shows the scenario in the page."""
    from src.report.generate_html import render_report
    for scenario in ["A", "B", "C", "D", "E"]:
        html = render_report(_make_report_tree(scenario), _make_metadata(scenario))
        assert scenario in html, f"Scenario {scenario} not found in HTML"


def test_render_report_satisfaction_percentages():
    """render_report includes satisfaction percentages as numeric text."""
    from src.report.generate_html import render_report
    html = render_report(_make_report_tree(), _make_metadata())
    # Criteria have satisfaction_pct = 15, 30, 45, 60, 75
    for pct in [15, 30, 45, 60, 75]:
        assert f"{pct}%" in html, f"Missing {pct}% in HTML"


def test_render_report_evidence_items_present():
    """render_report includes evidence item titles and details."""
    from src.report.generate_html import render_report
    html = render_report(_make_report_tree(), _make_metadata())
    assert "Evidence item 1.1.1" in html
    assert "Detail with numbers" in html


def test_render_report_references_rendered():
    """render_report includes source references."""
    from src.report.generate_html import render_report
    html = render_report(_make_report_tree(), _make_metadata())
    assert "Test Source" in html


def test_render_report_methodology_present():
    """render_report includes a methodology section."""
    from src.report.generate_html import render_report
    html = render_report(_make_report_tree(), _make_metadata())
    assert "Methodology" in html
    assert "five-criterion" in html.lower() or "five criteria" in html.lower() or "five AGI criteria" in html


def test_render_report_handles_empty_clusters():
    """render_report does not crash when criteria have no clusters."""
    from src.report.generate_html import render_report
    tree = _make_report_tree()
    for criterion in tree["criteria"]:
        criterion["clusters"] = []
    html = render_report(tree, _make_metadata())
    assert "<!DOCTYPE html>" in html


def test_render_report_html_escaping():
    """render_report escapes HTML special characters in content."""
    from src.report.generate_html import render_report
    tree = _make_report_tree()
    tree["executive_summary"]["summary"] = "AI > humans & <b>very smart</b>"
    html = render_report(tree, _make_metadata())
    # Raw < > should not appear unescaped in the rendered content
    assert "<b>very smart</b>" not in html
    assert "&amp;" in html or "&lt;" in html


def test_scenario_color_all_defined():
    """All standard scenario identifiers have defined colors."""
    from src.report.generate_html import SCENARIO_COLORS
    for scenario in ["A", "A→B", "B", "B→C", "C", "C→D", "D", "D→E", "E"]:
        assert scenario in SCENARIO_COLORS, f"Missing color for scenario {scenario}"
