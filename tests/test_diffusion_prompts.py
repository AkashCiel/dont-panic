"""Tests for diffusion prompt helpers."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_diffusion_framework_loads():
    from src.process.diffusion_prompts import get_diffusion_framework_text

    text = get_diffusion_framework_text()
    assert len(text) > 3000
    assert "Context Integrity" in text
    assert "Diffusion" in text or "diffusion" in text


def test_diffusion_wave1_prompts_build():
    from src.process.diffusion_prompts import build_diffusion_wave1_system_prompt, build_diffusion_wave1_user_prompt

    sys_p = build_diffusion_wave1_system_prompt()
    assert "JSON" in sys_p
    user_p = build_diffusion_wave1_user_prompt(
        source_id=21,
        source_name="SEC EDGAR",
        category="Financial",
        weight_default=5,
        items=[{"id": 1, "title": "t", "content": "c", "url": "https://x.com", "published_at": None}],
    )
    assert "SEC EDGAR" in user_p
    assert "Item 1" in user_p


def test_cognitive_context_block_empty():
    from src.process.diffusion_prompts import format_cognitive_context_block

    block = format_cognitive_context_block(None)
    assert "COGNITIVE TRACK CONTEXT" in block
    assert "not available" in block.lower() or "No cognitive" in block
