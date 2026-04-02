# TECHNICAL.md — AGI Capability Tracker

> **Living document.** This file describes the system as it is implemented, not as aspirationally intended. Updated with every significant implementation change.

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Actions (Scheduled)                    │
│                                                                  │
│   ┌─────────────────┐           ┌──────────────────────────┐    │
│   │  fetch.yml      │           │  report.yml              │    │
│   │  (daily, 06:00) │           │  (every 3 days, 08:00)   │    │
│   └────────┬────────┘           └──────────┬───────────────┘    │
└────────────┼────────────────────────────────┼────────────────────┘
             │                                │
             ▼                                ▼
┌────────────────────┐          ┌─────────────────────────────────┐
│   src/fetch/       │          │   src/process/                  │
│   main.py          │          │   main.py                       │
│                    │          │                                 │
│  rss_fetcher.py    │          │  wave1.py ──► wave2.py          │
│  api_fetcher.py    │          │                                 │
│  csv_fetcher.py    │          │  src/llm/                       │
│  graphql_fetcher   │          │  openai_provider.py             │
│  openreview_fetch  │          │  (Batch API)                    │
│  scrape_fetcher    │          └──────────┬──────────────────────┘
└────────┬───────────┘                     │
         │                                 │
         ▼                                 ▼
┌────────────────────────────────────────────────┐
│           Neon PostgreSQL                       │
│                                                 │
│  sources         fetched_items    wave1_outputs │
│  fetch_logs      reports                        │
└────────────────────┬───────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  src/report/          │
         │  generate_html.py     │
         │  → output/index.html  │
         └───────────┬───────────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
  ┌──────────────┐    ┌──────────────────┐
  │ GitHub Pages │    │ Telegram Bot API │
  │ (index.html) │    │ (notifications)  │
  └──────────────┘    └──────────────────┘
```

**Data flow:** 20 sources → fetch jobs store raw items in PostgreSQL → every 3 days, Wave 1 sends items to OpenAI Batch API for claim extraction → Wave 2 synthesises claims into a report tree → HTML is generated → deployed to GitHub Pages → Telegram notifications sent at each step.

**Dependencies:** Declared in `pyproject.toml` with `uv.lock`. Root `requirements.txt` is generated via `uv export` (runtime dependencies only; used by GitHub Actions and plain `pip` installs). Local development: `uv sync --extra dev`; optional OpenReview support: `uv sync --extra openreview`.

---

## 2. Database Schema

Executed via `db_migrations/001_initial_schema.sql`.

```sql
-- Source registry
CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    fetch_method VARCHAR(50) NOT NULL,  -- 'rss','rest_api','csv','graphql','sdk','scrape'
    url TEXT,
    weight_default INTEGER DEFAULT 3 CHECK (weight_default BETWEEN 1 AND 5),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Raw fetched content
CREATE TABLE fetched_items (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES sources(id),
    external_id VARCHAR(500),       -- URL, DOI, native ID from source
    title TEXT,
    content TEXT,                   -- abstract, summary, or full text (truncated)
    url TEXT,
    published_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT NOW(),
    fetch_cycle_id VARCHAR(50),     -- groups items from same fetch run
    processed BOOLEAN DEFAULT false,
    UNIQUE(source_id, external_id)  -- deduplication key
);

-- Wave 1 LLM outputs (claim extraction)
CREATE TABLE wave1_outputs (
    id SERIAL PRIMARY KEY,
    report_cycle_id VARCHAR(50) NOT NULL,
    fetched_item_id INTEGER REFERENCES fetched_items(id),
    source_weight INTEGER CHECK (source_weight BETWEEN 1 AND 5),
    weight_justification TEXT,
    claims JSONB NOT NULL,          -- array of {claim, criterion, evidence_type, confidence, notes}
    model_used VARCHAR(100),
    tokens_used INTEGER,
    cost_usd NUMERIC(10,6),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Final reports
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    report_cycle_id VARCHAR(50) UNIQUE NOT NULL,
    report_tree JSONB NOT NULL,     -- full three-layer tree structure
    scenario_assessment VARCHAR(10),
    model_used VARCHAR(100),
    total_cost_usd NUMERIC(10,4),
    items_analysed INTEGER,
    sources_covered INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Per-source fetch logs
CREATE TABLE fetch_logs (
    id SERIAL PRIMARY KEY,
    fetch_cycle_id VARCHAR(50) NOT NULL,
    source_id INTEGER REFERENCES sources(id),
    status VARCHAR(20) NOT NULL,    -- 'success', 'warning', 'error'
    items_found INTEGER DEFAULT 0,
    error_message TEXT,
    duration_seconds NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_fetched_items_source_published ON fetched_items(source_id, published_at);
CREATE INDEX idx_fetched_items_cycle ON fetched_items(fetch_cycle_id);
CREATE INDEX idx_fetched_items_processed ON fetched_items(processed, fetched_at);
CREATE INDEX idx_wave1_outputs_cycle ON wave1_outputs(report_cycle_id);
```

**Deduplication:** Primary key is `(source_id, external_id)`. For RSS feeds, `external_id` = item link/guid. For APIs, it's the source's native ID. Inserts use `ON CONFLICT DO NOTHING`.

### Connection pool and stale connections

All DB access goes through `src/db/connection.py` (`ThreadedConnectionPool`, min 1 / max 10 connections).

- **Checkout validation:** Before use, each connection from the pool is checked with `SELECT 1`. If the server closed the socket (e.g. long idle during OpenAI Batch API polling), the connection is dropped (`putconn(..., close=True)`) and another is taken, up to five attempts.
- **After errors:** On `OperationalError` or `InterfaceError` during work, rollback is attempted only if safe; the connection is then discarded from the pool so it is not reused.
- **Retry:** `execute_query`, `execute_non_query`, `execute_returning`, and `execute_many` retry once on `OperationalError` so a single lost connection does not fail the whole job without a second attempt.

This mitigates Neon/network idle timeouts; it does not change OpenAI Batch retry behavior (batch jobs still fail if the batch itself errors).

---

## 3. Source Registry

All 20 sources seeded via `src/db/seed_sources.py`.

| ID | Source | Category | Fetch Method | Default Weight | Auth Required |
|----|--------|----------|-------------|----------------|---------------|
| 1 | arXiv cs.AI | Papers | rss | 4 | None |
| 2 | arXiv cs.LG | Papers | rss | 4 | None |
| 3 | arXiv cs.CL | Papers | rss | 4 | None |
| 4 | Semantic Scholar | Papers | rest_api | 5 | `SEMANTIC_SCHOLAR_API_KEY` (optional, 1 RPS unauthenticated) |
| 5 | OpenReview | Papers | sdk | 5 | `OPENREVIEW_USERNAME`, `OPENREVIEW_PASSWORD` |
| 6 | Epoch AI datasets | Quantitative | csv | 5 | None |
| 7 | OpenAI blog | Lab blog | rss | 4 | None |
| 8 | Google DeepMind blog | Lab blog | rss | 4 | None |
| 9 | Anthropic research | Lab blog | rss | 4 | None (uses Olshansk scraper feed) |
| 10 | Meta AI (FAIR) | Lab blog | rss | 4 | None |
| 11 | DeepSeek releases | Lab releases | rest_api | 3 | `GITHUB_TOKEN` (optional, higher rate limits) |
| 12 | ARC-AGI leaderboard | Benchmark | scrape | 5 | None |
| 13 | Epoch AI Benchmarking Hub | Benchmark | csv | 5 | None |
| 14 | HuggingFace Open LLM Leaderboard | Benchmark | rest_api | 2 | None |
| 15 | SWE-bench | Benchmark | scrape | 2 | None (GitHub API) |
| 16 | Import AI newsletter | Newsletter | rss | 3 | None |
| 17 | Interconnects newsletter | Newsletter | rss | 3 | None |
| 18 | Zvi Mowshowitz AI roundup | Newsletter | rss | 3 | None |
| 19 | UK AI Safety Institute | Institutional | scrape | 2 | None |
| 20 | LessWrong | Community | graphql | 1 | None |

**Note on weights:** The LLM is instructed to assign its own weight per-call (1-5), overriding the default. The default is used as a hint and for seeding.

**Known source quirks:**
- arXiv RSS: 50-item limit per feed, 3s delay between requests required
- LessWrong: GraphQL API, filter `baseScore > 30` for quality
- OpenReview: Requires credentials; skips gracefully if not configured
- ARC-AGI: No structured API; HTML scraping may break on layout changes
- Epoch AI: CSVs accessed directly; URL may need updating if site restructures
- HuggingFace leaderboard datasets API (`open-llm-leaderboard/contents`) requires `datasets` package; implementation uses HF model API instead as a fallback

---

## 4. API Integrations

### arXiv (RSS)
- **Endpoint:** `https://arxiv.org/rss/cs.AI`, `/cs.LG`, `/cs.CL`
- **Auth:** None
- **Rate limit:** 3s delay between requests (arXiv policy)
- **Response format:** RSS/Atom XML parsed by `feedparser`
- **Error handling:** Retry once after 5s on connection error; log and continue on failure

### Semantic Scholar
- **Endpoint:** `https://api.semanticscholar.org/graph/v1/paper/search`
- **Auth:** `x-api-key` header (optional; 100 RPS authenticated, ~1 RPS unauthenticated)
- **Rate limit:** 1 RPS (enforced via `time.sleep(1)`)
- **Queries:** "AI reasoning", "world models", "causal reasoning", "self-directed learning"
- **Fields requested:** `paperId,title,abstract,url,year,publicationDate`
- **Pagination:** `limit=25` per query, no pagination beyond first page

### GitHub API (DeepSeek, SWE-bench)
- **Endpoint:** `https://api.github.com/orgs/deepseek-ai/repos`, `https://api.github.com/repos/SWE-bench/swe-bench.github.io/contents/`
- **Auth:** `Authorization: Bearer {GITHUB_TOKEN}` (optional; 5,000/hr authenticated)
- **Rate limit:** 5,000/hr authenticated, 60/hr unauthenticated
- **Error handling:** HTTP 403 (rate limit) triggers 60s backoff

### HuggingFace API
- **Endpoint:** `https://huggingface.co/api/models?sort=downloads&limit=20&filter=text-generation`
- **Auth:** None for public models
- **Rate limit:** Default 1s delay

### LessWrong GraphQL
- **Endpoint:** `https://www.lesswrong.com/graphql`
- **Auth:** None
- **Query:** `posts(input: { terms: { view: "new", limit: 50 } })` with fields `_id, title, postedAt, baseScore, commentCount, pageUrl`
- **Filter:** `baseScore > 30`

### OpenAI Batch API
- **Endpoint:** `https://api.openai.com/v1/batches`
- **Auth:** `Authorization: Bearer {OPENAI_API_KEY}`
- **Model:** `gpt-4o`
- **Pricing (batch, 50% off):** Input $1.25/1M tokens, Output $5.00/1M tokens
- **Completion window:** 24h (usually much faster)
- **Flow:** Create JSONL → upload as file → create batch → poll every 30s → download output file
- **Error handling:** Individual request errors logged; failed requests don't abort the batch

### Telegram Bot API
- **Endpoint:** `https://api.telegram.org/bot{token}/sendMessage`
- **Auth:** Bot token in URL
- **Parse mode:** HTML
- **Timeout:** 15s per request
- **Error handling:** Log and continue; never block main pipeline

---

## 5. LLM Prompt Architecture

### Framework Document
The full `framework/agi_evaluation_framework.md` is embedded in both Wave 1 and Wave 2 system prompts. This file is ~14,000 tokens. The framework defines the five AGI criteria, five scenarios (A–E), evaluation guides, and failure signatures.

**Loading:** `src/process/prompts.py:get_framework_text()` reads the file at call time. File path is computed relative to the module's `__file__`.

### Wave 1 System Prompt
Structure:
```
[Full framework text]

## Source Weight Guidelines
[Weight table 1-5]

## Your Task
[Instructions to extract claims as JSON]
[Output schema]
```

### Wave 1 User Prompt
Per batch of 1–12 items from one source:
```
Source: {name} (ID: {id}, Category: {category})
Default weight: {weight}

Content items to analyze:

[Item 1]
Title: ...
URL: ...
Date: ...
Content: ... (truncated at 2000 chars)

---

[Item 2]
...
```

### Wave 2 System Prompt
Structure:
```
[Full framework text]

## Your Task
[Instructions to synthesise claim document into report tree JSON]
[Full report tree schema with all fields]
[Scenario definitions A through E]
```

### Wave 2 User Prompt
```
Report cycle: {id}
Period: up to {date}
Total items analyzed: {n}
Sources covered: {n}

## Weighted Claims from All Sources

### Source weight: 5/5
[weight justification]
- [C1] [high] [benchmark_score] GPT-5 achieves 92% on GPQA — ...
...
```

### Context Window Handling
If the Wave 2 claims document exceeds ~80,000 characters (~20,000 tokens), the pipeline splits into:
1. Five parallel Wave 2 calls, one per criterion → each produces a criterion branch JSON
2. One final synthesis call that takes all five criterion JSONs → produces executive summary + cross-criterion analysis

### Response Format
All LLM calls use `response_format: {"type": "json_object"}` to enforce JSON output. Parsing uses `json.loads()` with error handling.

---

## 6. Report Tree Schema

```json
{
  "executive_summary": {
    "id": "exec",
    "title": "Executive Summary",
    "summary": "string (3-4 sentences)",
    "scenario_assessment": "A|A→B|B|B→C|C|C→D|D|D→E|E",
    "scenario_rationale": "string (2-3 sentences)"
  },
  "criteria": [
    {
      "id": "c1",
      "title": "Criterion 1: Unrestricted Intellectual Scope",
      "summary": "string (2-3 sentences)",
      "satisfaction_pct": 0,
      "clusters": [
        {
          "id": "c1.1",
          "title": "string",
          "summary": "string (paragraph)",
          "items": [
            {
              "id": "c1.1.1",
              "title": "string",
              "detail": "string (detailed with numbers)",
              "references": [
                {
                  "source": "string",
                  "url": "string",
                  "date": "YYYY-MM-DD",
                  "weight": 1
                }
              ]
            }
          ]
        }
      ]
    }
  ],
  "cross_criterion_analysis": {
    "id": "cross",
    "title": "Cross-Criterion Analysis",
    "summary": "string (paragraph on interdependencies)"
  }
}
```

**Criteria IDs:** `c1` through `c5`. Cluster IDs: `c1.1`, `c1.2`, etc. Item IDs: `c1.1.1`, etc.

**Report is saved to:**
1. PostgreSQL `reports` table (full JSON in `report_tree` JSONB column)
2. `output/latest_report.json` (for HTML generator)

---

## 7. GitHub Actions Workflows

### fetch.yml — Daily Fetch
- **Trigger:** Cron `0 6 * * *` (06:00 UTC daily) + `workflow_dispatch`
- **Timeout:** 30 minutes
- **Steps:** Checkout → Python 3.12 → `pip install -r requirements.txt` → `python src/fetch/main.py` (`requirements.txt` matches the uv lock export; see README)
- **Secrets needed:** `DATABASE_URL`, `SEMANTIC_SCHOLAR_API_KEY`, `GH_API_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `OPENREVIEW_USERNAME`, `OPENREVIEW_PASSWORD`
- **Note:** `GITHUB_TOKEN` is a special GitHub Actions token; the workflow uses `GH_API_TOKEN` for the GitHub API requests to avoid naming collision

### report.yml — Report Generation
- **Trigger:** Cron `0 8 */3 * *` (08:00 UTC every 3 days) + `workflow_dispatch`
- **Timeout:** 120 minutes (Batch API can take up to 24h; 2h is the practical fast-path timeout)
- **Steps:** Checkout → Python 3.12 → install → `python src/process/main.py` → `python src/report/generate_html.py` → deploy to `gh-pages` branch via `peaceiris/actions-gh-pages@v3`
- **Secrets needed:** `DATABASE_URL`, `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- **Output:** `output/index.html` deployed to GitHub Pages

### docs-metadata.yml — PR documentation reminder
- **Trigger:** `pull_request` targeting `main`
- **Purpose:** If the PR changes implementation paths (`src/`, `tests/`, `.github/workflows/`, `pyproject.toml`, or `requirements.txt`), it must also change `README.md` or `TECHNICAL.md` in the same PR (so user-facing and technical docs stay aligned). **Bypass:** include `[docs-skip]` in any commit message in the PR, or set `SKIP_DOCS_CHECK=1` when running the check script locally / in a custom job (use sparingly).

---

## 8. Telegram Notification Templates

### Fetch Summary (after daily fetch)
```
📥 Fetch cycle: 2025-01-15 06:02 UTC
✅ 18/20 sources OK
⚠️ OpenReview: credentials not configured
❌ ARC-AGI leaderboard: Connection timeout
New items: 147
```

### High-Signal Alert (weight ≥ 4 source publishes)
```
🔔 High-signal update detected
Source: OpenAI blog (weight 4)
Title: "GPT-5 System Card"
```

### Wave 1 Summary
```
🔬 Wave 1 complete: 2025-01-15
Sources processed: 147 items from 18 sources
Claims extracted: 312
By criterion: C1:89 | C2:74 | C3:51 | C4:38 | C5:60
Batch API cost: $0.4821
Duration: 4.2 min
```

### Wave 2 Summary
```
📊 Report generated: 2025-01-15
Scenario assessment: A→B
Report URL: https://username.github.io/dont-panic/
Batch API cost: $0.3104
Duration: 6.1 min
```

### Error
```
❌ Error in Wave 1
Batch abc123 ended with status: failed
```

---

## 9. Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Neon PostgreSQL connection string (`postgresql://...?sslmode=require`) |
| `LLM_PROVIDER` | No (default: `openai`) | LLM provider to use |
| `LLM_MODEL` | No (default: `gpt-4o`) | Model name |
| `OPENAI_API_KEY` | Yes (for processing) | OpenAI API key |
| `TELEGRAM_BOT_TOKEN` | No | Telegram bot token (notifications disabled if absent) |
| `TELEGRAM_CHAT_ID` | No | Telegram chat ID for notifications |
| `SEMANTIC_SCHOLAR_API_KEY` | No | Semantic Scholar API key (unauthenticated rate limit applies if absent) |
| `OPENREVIEW_USERNAME` | No | OpenReview account username (source skipped if absent) |
| `OPENREVIEW_PASSWORD` | No | OpenReview account password |
| `GITHUB_TOKEN` | No | GitHub personal access token for API calls |
| `REPORT_INTERVAL_DAYS` | No (default: `3`) | Days between report generation runs |
| `FETCH_SCHEDULE_UTC` | No (default: `0600`) | Fetch schedule time in UTC (informational only; actual schedule in fetch.yml) |

---

## 10. Known Limitations and Quirks

1. **OpenAI Batch API polling:** The processing job polls every 30 seconds but may time out at the 120-minute GitHub Actions limit. If the batch takes longer, the workflow will fail. Recommendation: re-run manually or increase timeout.

2. **Wave 1 items_processed count:** The `sources_covered` field in the reports table is not accurately populated (stored as 0). A future improvement would join wave1_outputs with fetched_items → sources.

3. **ARC-AGI scraping is fragile:** The `arcprize.org/leaderboard` page structure can change without notice. The scraper has defensive fallbacks but may return empty results. Consider requesting a structured data feed from ARC Prize.

4. **Epoch AI CSV URLs:** The download URLs (`epoch.ai/data/ai-models.csv`) are assumed based on site structure. If they change, update `csv_fetcher.py`. The fetcher tries multiple URL patterns.

5. **OpenReview SDK:** The `openreview-py` package is an optional extra (`uv sync --extra openreview` or `pip install openreview-py`). It is not in the default `requirements.txt` export. The fetcher gracefully skips if the package is unavailable.

6. **Content truncation:** Item content is truncated at 2,000 characters in the Wave 1 user prompt. Abstracts are typically 150–300 words (~1,000 characters), so this is adequate. Full blog posts may be truncated significantly.

7. **LessWrong rate limits:** No documented rate limits; 1s delay between calls. If rate-limited, add exponential backoff.

8. **GitHub Actions GITHUB_TOKEN vs GH_API_TOKEN:** The `GITHUB_TOKEN` secret in GitHub Actions is a special token injected automatically. For GitHub API calls in the fetch script, use the `GH_API_TOKEN` secret (a PAT) to avoid naming conflicts.

9. **No retry on batch failure:** If an OpenAI Batch API job fails, the processing pipeline raises an exception. There is no automatic retry. Re-run the workflow manually.

10. **HTML generator reads `output/latest_report.json`:** This file is written by `process/main.py` before the HTML generator runs. If processing fails mid-way, this file may be absent or stale. The HTML generator handles missing files gracefully (shows an error page).

11. **Repository `scripts/` folder:** The root `scripts/` path is listed in `.gitignore` for local, untracked one-off utilities. Anything intended for the team or CI should live under `src/`, `tests/`, or `.github/scripts/` (tracked).

---

## 11. Cost Estimates

Based on expected item volumes and prompt sizes.

### Assumptions
- 20 sources, averaging ~10 new items/day each = ~200 items/day
- Over 3-day cycle: ~600 items
- Wave 1: ~50 API calls (one per source-batch), ~3,000 tokens input + 1,000 tokens output per call
- Wave 2: 1 API call, ~15,000 tokens input + 8,000 tokens output

### Per-Cycle Cost Estimate

| Component | Calls | Avg Input Tokens | Avg Output Tokens | Cost (batch pricing) |
|-----------|-------|-----------------|-------------------|---------------------|
| Wave 1 | ~50 | 3,000 | 1,000 | ~$0.25 |
| Wave 2 | 1 | 15,000 | 8,000 | ~$0.06 |
| **Total** | | | | **~$0.31/cycle** |

**Monthly cost estimate:** ~10 cycles/month × $0.31 = **~$3.10/month**

These estimates will be refined once real token usage data is available from the `wave1_outputs.tokens_used` and `wave1_outputs.cost_usd` columns.

### Free Tier Constraints
- **Neon PostgreSQL free tier:** 0.5 GB storage, 1 compute unit. Should be sufficient for months of operation at this volume.
- **GitHub Actions free tier:** 2,000 minutes/month (public repos: unlimited). Each cycle: ~10 min fetch + ~30 min process = ~40 min/cycle × 10 cycles = 400 min/month on private repos; unlimited on public.

---

## 12. Diffusion Track

The diffusion pipeline runs alongside the cognitive track: it analyses how AI capabilities spread through society (enterprise, government, individuals). It shares `fetched_items` with cognitive sources where configured (`sources.track`, shared source IDs in `src/db/diffusion_constants.py`).

- **Migration:** `db_migrations/002_diffusion_track.sql` adds `track` on `sources`, `wave1_outputs`, `reports`; `fetched_items.diffusion_processed`; tables `diffusion_wave1_outputs` and `diffusion_reports`.
- **Seed:** `python src/db/seed_sources.py` — 20 cognitive + 12 diffusion sources (ids 21–32). Requires migration 002 first.
- **Fetch:** `python src/fetch/main.py [--track all|cognitive|diffusion]` — default `all`. New fetch methods: `sec_edgar`, `sam_gov`, `usaspending`, `ted_eu`, `cloudflare_radar`, `rss_ai`, `economic_index`. Cloudflare Radar (source 26) is skipped if the last successful fetch was within 7 days; Anthropic Economic Index (32) within 30 days.
- **Process:** `python src/process/diffusion_main.py` — Wave 1/2 use `diffusion_prompts.py` and `framework/ai_diffusion_framework.md`. Wave 2 pulls context from the latest cognitive report in `reports` (`track = 'cognitive'`).
- **Output:** `output/latest_diffusion_report.json`, `output/diffusion/index.html`. Cognitive report: `output/cognitive/index.html`. Landing: `output/index.html` via `python src/report/generate_landing.py`.
- **CI:** `.github/workflows/diffusion_report.yml` schedules diffusion processing; `report.yml` and `diffusion_report.yml` should both run `generate_landing.py` so Pages always has a root index.

### Environment (diffusion)

| Variable | Required | Purpose |
|----------|----------|---------|
| `SAM_GOV_API_KEY` | No | SAM.gov API; source 23 skipped / empty if absent |
| `CLOUDFLARE_API_TOKEN` | No | Cloudflare Radar; source 26 empty if absent |
| `DIFFUSION_REPORT_INTERVAL_DAYS` | No (default `3`) | Informational; schedule is in workflow cron |

---

## 13. Discrepancies Found During Diffusion Track Setup

1. **SPEC vs seed path:** `SPEC_Diffusion.md` refers to `scripts/seed_sources.py` in one place; the project uses `src/db/seed_sources.py` consistently with the cognitive codebase.
2. **HTML paths:** The cognitive report was previously written to `output/index.html`. It is now written to `output/cognitive/index.html` with `output/index.html` as a small landing page linking both tracks. Update bookmarks and any external links to the cognitive report URL.
3. **`sources_covered` in cognitive reports:** Still populated as `0` from `process/main.py` (pre-existing quirk); diffusion pipeline computes `sources_covered` from Wave 1 joins.

---

*Last updated: 2026-03-31 — diffusion track implementation (fetch, process, HTML, workflows)*
