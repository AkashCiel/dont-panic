"""Shared constants for the diffusion track (shared cognitive + diffusion-only sources)."""

# Source IDs relevant to both tracks (lab blogs, Epoch datasets, newsletters per SPEC).
SHARED_DIFFUSION_SOURCE_IDS: tuple[int, ...] = (6, 7, 8, 9, 10, 16, 17, 18)

# Diffusion-only sources (v1): IDs 21–32 after seeding.
DIFFUSION_ONLY_SOURCE_IDS: tuple[int, ...] = tuple(range(21, 33))
