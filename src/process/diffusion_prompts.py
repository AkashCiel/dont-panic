"""Backward-compatible re-exports — diffusion prompts live in src.prompts.diffusion."""

from src.prompts.diffusion import (
    build_diffusion_wave1_system_prompt,
    build_diffusion_wave1_user_prompt,
    build_diffusion_wave2_merge_prompt,
    build_diffusion_wave2_partial_prompt,
    build_diffusion_wave2_system_prompt,
    build_diffusion_wave2_user_prompt,
    format_cognitive_context_block,
    get_diffusion_framework_text,
)

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
