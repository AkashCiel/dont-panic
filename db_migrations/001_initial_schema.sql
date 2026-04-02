-- AGI Capability Tracker — Initial Schema
-- Run: psql $DATABASE_URL -f db_migrations/001_initial_schema.sql

CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    fetch_method VARCHAR(50) NOT NULL,
    url TEXT,
    weight_default INTEGER DEFAULT 3 CHECK (weight_default BETWEEN 1 AND 5),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fetched_items (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES sources(id),
    external_id VARCHAR(500),
    title TEXT,
    content TEXT,
    url TEXT,
    published_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT NOW(),
    fetch_cycle_id VARCHAR(50),
    processed BOOLEAN DEFAULT false,
    UNIQUE(source_id, external_id)
);

CREATE TABLE IF NOT EXISTS wave1_outputs (
    id SERIAL PRIMARY KEY,
    report_cycle_id VARCHAR(50) NOT NULL,
    fetched_item_id INTEGER REFERENCES fetched_items(id),
    source_weight INTEGER CHECK (source_weight BETWEEN 1 AND 5),
    weight_justification TEXT,
    claims JSONB NOT NULL,
    model_used VARCHAR(100),
    tokens_used INTEGER,
    cost_usd NUMERIC(10,6),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    report_cycle_id VARCHAR(50) UNIQUE NOT NULL,
    report_tree JSONB NOT NULL,
    scenario_assessment VARCHAR(10),
    model_used VARCHAR(100),
    total_cost_usd NUMERIC(10,4),
    items_analysed INTEGER,
    sources_covered INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fetch_logs (
    id SERIAL PRIMARY KEY,
    fetch_cycle_id VARCHAR(50) NOT NULL,
    source_id INTEGER REFERENCES sources(id),
    status VARCHAR(20) NOT NULL,
    items_found INTEGER DEFAULT 0,
    error_message TEXT,
    duration_seconds NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_fetched_items_source_published ON fetched_items(source_id, published_at);
CREATE INDEX IF NOT EXISTS idx_fetched_items_cycle ON fetched_items(fetch_cycle_id);
CREATE INDEX IF NOT EXISTS idx_fetched_items_processed ON fetched_items(processed, fetched_at);
CREATE INDEX IF NOT EXISTS idx_wave1_outputs_cycle ON wave1_outputs(report_cycle_id);
