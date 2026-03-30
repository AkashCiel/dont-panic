"""Tests for fetcher modules — mocked network calls."""
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── RSS fetcher ───────────────────────────────────────────────────────────────

def _make_entry(title, link, summary, published_parsed=None):
    entry = MagicMock()
    entry.title = title
    entry.link = link
    entry.id = link
    entry.summary = summary
    entry.published = "Mon, 01 Jan 2025 00:00:00 +0000"
    entry.published_parsed = published_parsed or (2025, 1, 1, 0, 0, 0, 0, 1, 0)
    entry.content = None
    return entry


def test_rss_fetcher_parses_basic_feed():
    """RSS fetcher returns correctly structured items."""
    mock_feed = MagicMock()
    mock_feed.bozo = False
    mock_feed.entries = [
        _make_entry(
            title="<b>Scaling Laws for Neural Networks</b>",
            link="https://arxiv.org/abs/2501.00001",
            summary="We study scaling laws...",
        )
    ]

    with patch("feedparser.parse", return_value=mock_feed), \
         patch("time.sleep"):
        from src.fetch.rss_fetcher import fetch_rss
        source = {"id": 1, "name": "arXiv cs.AI", "url": "https://arxiv.org/rss/cs.AI"}
        items = fetch_rss(source, "test-cycle-001")

    assert len(items) == 1
    assert items[0]["external_id"] == "https://arxiv.org/abs/2501.00001"
    assert items[0]["url"] == "https://arxiv.org/abs/2501.00001"
    # HTML should be stripped from title
    assert "<b>" not in items[0]["title"]
    assert items[0]["published_at"] is not None


def test_rss_fetcher_skips_entries_without_link():
    """RSS fetcher skips entries that have no link or id."""
    mock_feed = MagicMock()
    mock_feed.bozo = False
    entry = MagicMock()
    entry.link = None
    entry.id = None
    entry.title = "Orphaned entry"
    entry.summary = "No link"
    entry.content = None
    entry.published_parsed = (2025, 1, 1, 0, 0, 0, 0, 1, 0)
    mock_feed.entries = [entry]

    with patch("feedparser.parse", return_value=mock_feed), \
         patch("time.sleep"):
        from src.fetch.rss_fetcher import fetch_rss
        source = {"id": 7, "name": "OpenAI blog", "url": "https://openai.com/news/rss.xml"}
        items = fetch_rss(source, "test-cycle-002")

    assert items == []


def test_rss_fetcher_limits_to_50_entries():
    """RSS fetcher returns at most 50 entries."""
    mock_feed = MagicMock()
    mock_feed.bozo = False
    mock_feed.entries = [
        _make_entry(f"Paper {i}", f"https://example.com/{i}", "Abstract")
        for i in range(100)
    ]

    with patch("feedparser.parse", return_value=mock_feed), \
         patch("time.sleep"):
        from src.fetch.rss_fetcher import fetch_rss
        source = {"id": 1, "name": "arXiv cs.AI", "url": "https://arxiv.org/rss/cs.AI"}
        items = fetch_rss(source, "test-cycle-003")

    assert len(items) == 50


# ── GraphQL fetcher ───────────────────────────────────────────────────────────

def test_graphql_fetcher_filters_low_score_posts():
    """LessWrong fetcher only returns posts with baseScore > 30."""
    mock_response = {
        "data": {
            "posts": {
                "results": [
                    {"_id": "abc123", "title": "High score", "postedAt": "2025-01-01T00:00:00Z",
                     "baseScore": 75, "commentCount": 20, "pageUrl": "https://lesswrong.com/posts/abc123"},
                    {"_id": "def456", "title": "Low score", "postedAt": "2025-01-01T00:00:00Z",
                     "baseScore": 5, "commentCount": 1, "pageUrl": "https://lesswrong.com/posts/def456"},
                    {"_id": "ghi789", "title": "Borderline", "postedAt": "2025-01-01T00:00:00Z",
                     "baseScore": 30, "commentCount": 3, "pageUrl": "https://lesswrong.com/posts/ghi789"},
                ]
            }
        }
    }

    mock_resp = MagicMock()
    mock_resp.json.return_value = mock_response
    mock_resp.raise_for_status.return_value = None

    with patch("requests.post", return_value=mock_resp), \
         patch("time.sleep"):
        from src.fetch.graphql_fetcher import fetch_lesswrong
        source = {"id": 20, "name": "LessWrong", "url": "https://www.lesswrong.com/graphql"}
        items = fetch_lesswrong(source, "test-cycle-004")

    # Only the post with score=75 passes (score=30 is NOT > 30)
    assert len(items) == 1
    assert items[0]["external_id"] == "abc123"
    assert items[0]["title"] == "High score"


def test_graphql_fetcher_handles_empty_results():
    """LessWrong fetcher handles empty results gracefully."""
    mock_response = {"data": {"posts": {"results": []}}}
    mock_resp = MagicMock()
    mock_resp.json.return_value = mock_response
    mock_resp.raise_for_status.return_value = None

    with patch("requests.post", return_value=mock_resp), \
         patch("time.sleep"):
        from src.fetch.graphql_fetcher import fetch_lesswrong
        source = {"id": 20, "name": "LessWrong", "url": "https://www.lesswrong.com/graphql"}
        items = fetch_lesswrong(source, "test-cycle-005")

    assert items == []


# ── OpenReview fetcher ────────────────────────────────────────────────────────

def test_openreview_fetcher_skips_when_no_credentials():
    """OpenReview fetcher returns [] when credentials are absent."""
    from src.fetch.openreview_fetcher import fetch_openreview
    source = {"id": 5, "name": "OpenReview", "url": "https://openreview.net"}
    items = fetch_openreview(source, "test-cycle-006", username="", password="")
    assert items == []


def test_openreview_fetcher_skips_when_package_missing():
    """OpenReview fetcher returns [] when openreview-py is not installed."""
    with patch.dict("sys.modules", {"openreview": None}):
        # Re-import to test missing module path
        import importlib
        import src.fetch.openreview_fetcher as mod
        importlib.reload(mod)
        items = mod.fetch_openreview(
            {"id": 5, "name": "OpenReview"}, "test-cycle-007",
            username="user", password="pass"
        )
        assert items == []


# ── HTML generator ────────────────────────────────────────────────────────────

def test_html_generator_produces_valid_html():
    """HTML generator produces a complete page from sample report data."""
    from src.report.generate_html import render_report

    sample_tree = {
        "executive_summary": {
            "id": "exec",
            "title": "Executive Summary",
            "summary": "Current AI systems are in Scenario A.",
            "scenario_assessment": "A",
            "scenario_rationale": "No criteria fully satisfied.",
        },
        "criteria": [
            {
                "id": "c1",
                "title": "Criterion 1: Unrestricted Intellectual Scope",
                "summary": "Partial progress.",
                "satisfaction_pct": 40,
                "clusters": [
                    {
                        "id": "c1.1",
                        "title": "Benchmark Performance",
                        "summary": "Strong benchmarks across domains.",
                        "items": [
                            {
                                "id": "c1.1.1",
                                "title": "GPQA Diamond",
                                "detail": "Models achieving 80%+ on GPQA Diamond.",
                                "references": [
                                    {"source": "OpenAI blog", "url": "https://openai.com", "date": "2025-01-01", "weight": 4}
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
        "cross_criterion_analysis": {
            "id": "cross",
            "title": "Cross-Criterion Analysis",
            "summary": "Criteria remain largely unsatisfied.",
        },
    }
    metadata = {
        "report_cycle_id": "test-cycle-001",
        "created_at": "2025-01-01T00:00:00Z",
        "scenario_assessment": "A",
        "total_cost_usd": 1.23,
        "items_analysed": 150,
    }

    html = render_report(sample_tree, metadata)

    assert "<!DOCTYPE html>" in html
    assert "AGI Capability Tracker" in html
    assert "Executive Summary" in html
    assert "Criterion 1" in html
    assert "GPQA Diamond" in html
    assert "Scenario A" in html
    assert "40%" in html
