-- Diffusion track schema additions
-- Run: psql $DATABASE_URL -f src/db/migrations/002_diffusion_track.sql

ALTER TABLE sources ADD COLUMN IF NOT EXISTS track VARCHAR(20) DEFAULT 'cognitive';

UPDATE sources SET track = 'cognitive' WHERE track IS NULL;

ALTER TABLE wave1_outputs ADD COLUMN IF NOT EXISTS track VARCHAR(20) DEFAULT 'cognitive';

UPDATE wave1_outputs SET track = 'cognitive' WHERE track IS NULL;

ALTER TABLE reports ADD COLUMN IF NOT EXISTS track VARCHAR(20) DEFAULT 'cognitive';

UPDATE reports SET track = 'cognitive' WHERE track IS NULL;

ALTER TABLE fetched_items ADD COLUMN IF NOT EXISTS diffusion_processed BOOLEAN DEFAULT false;

UPDATE fetched_items SET diffusion_processed = false WHERE diffusion_processed IS NULL;

CREATE TABLE IF NOT EXISTS diffusion_wave1_outputs (
    id SERIAL PRIMARY KEY,
    report_cycle_id VARCHAR(50) NOT NULL,
    fetched_item_id INTEGER REFERENCES fetched_items(id),
    source_weight INTEGER CHECK (source_weight BETWEEN 1 AND 5),
    weight_justification TEXT,
    findings JSONB NOT NULL,
    model_used VARCHAR(100),
    tokens_used INTEGER,
    cost_usd NUMERIC(10,6),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS diffusion_reports (
    id SERIAL PRIMARY KEY,
    report_cycle_id VARCHAR(50) UNIQUE NOT NULL,
    report_tree JSONB NOT NULL,
    model_used VARCHAR(100),
    total_cost_usd NUMERIC(10,4),
    items_analysed INTEGER,
    sources_covered INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_diffusion_wave1_cycle ON diffusion_wave1_outputs(report_cycle_id);
CREATE INDEX IF NOT EXISTS idx_diffusion_reports_cycle ON diffusion_reports(report_cycle_id);
CREATE INDEX IF NOT EXISTS idx_sources_track ON sources(track);
CREATE INDEX IF NOT EXISTS idx_fetched_items_diffusion_processed ON fetched_items(diffusion_processed, fetched_at);
