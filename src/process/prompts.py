"""Backward-compatible re-exports — cognitive prompts live in src.prompts.cognitive."""

from src.prompts.cognitive import (
    build_wave1_system_prompt,
    build_wave1_user_prompt,
    build_wave2_system_prompt,
    build_wave2_user_prompt,
    get_framework_text,
)

__all__ = [
    "build_wave1_system_prompt",
    "build_wave1_user_prompt",
    "build_wave2_system_prompt",
    "build_wave2_user_prompt",
    "get_framework_text",
]
