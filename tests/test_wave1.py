"""Tests for Wave 1 prompt building and output schema validation."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_build_wave1_user_prompt_includes_source_info():
    """Wave 1 user prompt includes source name and item titles."""
    from src.process.prompts import build_wave1_user_prompt

    items = [
        {
            "id": 1,
            "title": "Scaling Laws for AI",
            "content": "We present scaling laws...",
            "url": "https://arxiv.org/abs/2501.00001",
            "published_at": None,
        }
    ]
    prompt = build_wave1_user_prompt(
        source_id=1,
        source_name="arXiv cs.AI",
        category="Papers",
        weight_default=4,
        items=items,
    )
    assert "arXiv cs.AI" in prompt
    assert "Scaling Laws for AI" in prompt
    assert "We present scaling laws" in prompt
    assert "Papers" in prompt


def test_build_wave1_user_prompt_multiple_items():
    """Wave 1 user prompt correctly formats multiple items."""
    from src.process.prompts import build_wave1_user_prompt

    items = [
        {"id": i, "title": f"Paper {i}", "content": f"Content {i}", "url": f"https://example.com/{i}", "published_at": None}
        for i in range(5)
    ]
    prompt = build_wave1_user_prompt(
        source_id=7,
        source_name="OpenAI blog",
        category="Lab blog",
        weight_default=4,
        items=items,
    )
    assert "[Item 1]" in prompt
    assert "[Item 5]" in prompt
    assert "Paper 0" in prompt
    assert "Paper 4" in prompt


def test_build_wave1_user_prompt_truncates_long_content():
    """Wave 1 user prompt truncates item content at 2000 chars."""
    from src.process.prompts import build_wave1_user_prompt

    long_content = "A" * 5000
    items = [{"id": 1, "title": "Test", "content": long_content, "url": "https://x.com", "published_at": None}]
    prompt = build_wave1_user_prompt(
        source_id=1, source_name="test", category="test", weight_default=3, items=items
    )
    # The long content should be truncated
    assert "A" * 2001 not in prompt


def test_framework_text_is_loadable():
    """The AGI evaluation framework file exists and is non-trivial."""
    from src.process.prompts import get_framework_text
    text = get_framework_text()
    assert len(text) > 5000, f"Framework text too short: {len(text)} chars"
    assert "Criterion 1" in text
    assert "Criterion 5" in text
    assert "Epistemological" in text


def test_wave1_system_prompt_includes_framework():
    """Wave 1 system prompt embeds the framework document."""
    from src.process.prompts import build_wave1_system_prompt
    prompt = build_wave1_system_prompt()
    assert "Criterion 1" in prompt
    assert "Criterion 5" in prompt
    assert "Source Weight Guidelines" in prompt
    assert "json_object" not in prompt.lower()  # schema should be in prompt text


def test_wave1_output_schema_validation():
    """A valid Wave 1 JSON output passes schema checks."""
    import json

    valid_output = json.dumps({
        "source_id": 7,
        "source_name": "OpenAI blog",
        "source_weight": 4,
        "weight_justification": "Primary lab publication with first-party claims",
        "claims": [
            {
                "claim": "GPT-5 achieves 92.4% on GPQA Diamond",
                "criterion": 1,
                "evidence_type": "benchmark_score",
                "confidence": "high",
                "notes": "Self-reported; awaiting independent verification",
            }
        ],
    })

    parsed = json.loads(valid_output)
    assert "source_id" in parsed
    assert "claims" in parsed
    assert isinstance(parsed["claims"], list)

    for claim in parsed["claims"]:
        assert "claim" in claim
        assert "criterion" in claim
        assert claim["criterion"] in [1, 2, 3, 4, 5]
        assert "confidence" in claim
        assert claim["confidence"] in ["high", "medium", "low"]
        assert "evidence_type" in claim


def test_wave2_system_prompt_includes_scenario_definitions():
    """Wave 2 system prompt includes scenario definitions A through E."""
    from src.process.prompts import build_wave2_system_prompt
    prompt = build_wave2_system_prompt()
    for scenario in ["Scenario A", "Scenario B", "Scenario C", "Scenario D", "Scenario E"]:
        assert scenario in prompt, f"Missing: {scenario}"
