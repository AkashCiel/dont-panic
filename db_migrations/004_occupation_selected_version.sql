-- Audience scope for occupation artifacts (v1 social-distribution focus, etc.)
-- Run: psql $DATABASE_URL -f db_migrations/004_occupation_selected_version.sql

ALTER TABLE occupation_artifacts
    ADD COLUMN IF NOT EXISTS selected_for_version VARCHAR(32);

COMMENT ON COLUMN occupation_artifacts.selected_for_version IS
    'Set to version label (e.g. version 1) when included in a curated audience scope; NULL otherwise.';
