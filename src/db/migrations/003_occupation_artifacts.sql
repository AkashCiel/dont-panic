-- O*NET-derived occupation bundles for LLM downstream (one row per occupation).
-- Populate separately from O*NET export (e.g. MySQL dump → ETL script); table is empty after this migration.
-- Run: psql $DATABASE_URL -f src/db/migrations/003_occupation_artifacts.sql

CREATE TABLE IF NOT EXISTS occupation_artifacts (
    onetsoc_code VARCHAR(10) PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    -- Ordered list of tasks with optional survey ratings (from task_statements + task_ratings).
    -- Schema per element:
    --   task_id (number), task (string), task_type (string|null),
    --   sort_order (int, display order within occupation),
    --   incumbents_responding, date_updated, domain_source (optional),
    --   ratings: [ { scale_id, category, data_value, n, ... } ]  (from task_ratings; join task_categories for labels)
    tasks JSONB NOT NULL DEFAULT '[]'::jsonb,
    task_count INTEGER NOT NULL DEFAULT 0,
    source_label TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT occupation_artifacts_tasks_is_array CHECK (jsonb_typeof(tasks) = 'array'),
    CONSTRAINT occupation_artifacts_task_count_nonneg CHECK (task_count >= 0)
);

COMMENT ON TABLE occupation_artifacts IS
    'One curated record per O*NET-SOC occupation: official title/description plus JSON array of tasks (with optional ratings) for LLM prompts.';

CREATE INDEX IF NOT EXISTS idx_occupation_artifacts_title ON occupation_artifacts (title);

-- Optional: prefix search / title lookup (requires pg_trgm on Neon — enable extension if needed)
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- CREATE INDEX IF NOT EXISTS idx_occupation_artifacts_title_trgm ON occupation_artifacts USING gin (title gin_trgm_ops);
