# AI Diffusion Tracker — System Specification

## What This Document Is

This is the complete specification for extending the existing AGI Capability Tracker to include a **diffusion track** — tracking how AI capabilities propagate through society and predicting disruptions to societal patterns. Claude Code should implement everything described here. Where implementation details are unspecified, make reasonable decisions and document them in TECHNICAL.md.

**CRITICAL: Read this entire document before writing any code.**

---

## 0. Context: Existing System

An AGI Capability Tracker already exists in this repository. It has:

- **Fetch layer:** Daily scheduled jobs pulling content from ~20 sources (arXiv, Semantic Scholar, OpenReview, Epoch AI, lab blogs, benchmarks, newsletters, LessWrong, UK AISI). Fetchers organized by type: RSS, REST API, CSV download, GraphQL, web scrape, Python SDK.
- **Storage:** Neon PostgreSQL with tables: `sources`, `fetched_items`, `wave1_outputs`, `reports`, `fetch_logs`.
- **Processing:** Two-wave LLM pipeline using OpenAI Batch API. Wave 1 extracts weighted claims from each source. Wave 2 synthesizes claims into a three-layer expandable report tree.
- **Output:** Static HTML report deployed to GitHub Pages. Telegram notifications for fetch summaries, high-signal updates, and report generation.
- **Orchestration:** GitHub Actions workflows for daily fetch and periodic report generation.

The diffusion track **shares the fetch and storage infrastructure** but has its own analysis pipeline and outputs.

---

## 1. Pre-Implementation Steps

### 1.1 Inspect Current State

The repository may have been modified since initial build. Before making any changes:

1. `git fetch origin && git log --oneline -20` — review recent commits
2. `cat TECHNICAL.md` — understand current implementation details
3. `ls src/` — verify project structure matches expectations
4. `cat src/db/migrations/` — check all existing migrations
5. `python src/fetch/main.py --help` or read `src/fetch/main.py` — understand current fetch orchestration
6. Check `requirements.txt` for current dependencies
7. Verify the database schema by connecting and running `\dt` and `\d+ fetched_items` (or equivalent)

**Document any discrepancies** between the cognitive SPEC, TECHNICAL.md, and actual code in a section of TECHNICAL.md called "Discrepancies Found During Diffusion Track Setup."

### 1.2 Create a New Branch

All work MUST happen on a new branch:

```bash
git checkout main
git pull origin main
git checkout -b diffusion-track
```

**Never commit to main. Never push to main.** All changes go to the `diffusion-track` branch. The developer will review the diff and merge manually.

### 1.3 Do Not Modify Existing Cognitive Track Analysis

The following files must NOT be modified:

- `src/process/prompts.py` — cognitive track prompt templates (add diffusion prompts in a new file)
- `src/process/wave1.py` — cognitive track Wave 1 logic (add diffusion wave1 in a new file)
- `src/process/wave2.py` — cognitive track Wave 2 logic (add diffusion wave2 in a new file)
- `framework/agi_evaluation_framework.md` — cognitive track analytical framework

You MAY modify:

- `src/fetch/main.py` — to add new source fetchers (the fetch layer is shared)
- `src/db/models.py` — to add new database operations for diffusion tables
- `src/notify/telegram.py` — to add new notification types for diffusion
- `src/config.py` — to add new configuration variables
- Database migrations — add new migration files (never modify existing ones)
- GitHub Actions workflows — add new workflows for diffusion processing
- `requirements.txt` — add new dependencies if needed

---

## 2. New Data Sources for Diffusion Track

The diffusion track needs sources that cover: AI lab business activity, enterprise adoption, government procurement, regulatory actions, and market dynamics. Some existing cognitive sources are also relevant to diffusion (lab blogs announce partnerships, Epoch AI tracks revenue). These shared sources get analysed by BOTH the cognitive and diffusion pipelines — no need to fetch them twice.

### Sources Shared with Cognitive Track (already fetched)

These sources are already in the `sources` table. The diffusion pipeline will query `fetched_items` for these sources and analyse them with diffusion-specific prompts. No new fetchers needed.

| Existing Source ID | Relevance to Diffusion |
|---|---|
| 7 (OpenAI blog) | Partnership announcements, pricing changes, product launches, customer milestones |
| 8 (Google DeepMind blog) | Product integrations, enterprise AI strategy |
| 9 (Anthropic research/news) | Enterprise customer announcements, API changes, pricing |
| 10 (Meta AI) | Open-source release strategy, Llama ecosystem growth |
| 6 (Epoch AI datasets) | Company revenue data, compute investment trends |
| 16-18 (Newsletters) | Expert commentary on industry dynamics and adoption |

### New Sources to Add (12 for v1)

Add these to the `sources` table with `track = 'diffusion'` (see schema changes in Section 3). Implement fetch logic per source type.

| ID | Source | Category | Fetch Method | URL / Endpoint |
|----|--------|----------|-------------|----------------|
| 21 | SEC EDGAR Full-Text Search | Financial | REST API | `https://efts.sec.gov/LATEST/search-index?q=%22artificial+intelligence%22&dateRange=custom&startdt={start}&enddt={end}&forms=10-K,10-Q,8-K` — search for AI vendor mentions in public company filings. No auth. Rate limit: 10 req/sec. |
| 22 | Epoch AI Company Revenue | Financial | CSV download | `https://epoch.ai/data/ai_companies_revenue_reports.csv` — timestamped revenue datapoints for AI companies with source URLs and confidence ratings. CC-BY license. |
| 23 | SAM.gov Federal Procurement | Government | REST API | `https://api.sam.gov/prod/opportunities/v2/search?api_key={key}&keywords=artificial+intelligence,machine+learning,large+language+model&postedFrom={date}` — US federal contract opportunities. Free API key required (register at sam.gov). Rate limit: 1,000 req/day. |
| 24 | USAspending.gov | Government | REST API | `https://api.usaspending.gov/api/v2/search/spending_by_award/` — US federal spending data. No auth for basic access. Filter by NAICS codes 541511, 541512, 541519, 518210 and keyword "artificial intelligence". |
| 25 | TED EU Procurement | Government | REST API | `https://api.ted.europa.eu/v3/notices/search` — EU public procurement notices. Free API. Filter by CPV codes related to IT services and keywords "artificial intelligence", "machine learning". Updated 5x/week. |
| 26 | Cloudflare Radar AI Insights | Usage Metrics | REST API | `https://api.cloudflare.com/client/v4/radar/ai/bots/timeseries` and `https://api.cloudflare.com/client/v4/radar/ai/inference/timeseries` — AI bot traffic volumes, AI service popularity, model usage distribution. Free tier available. Auth via API token. |
| 27 | AWS AI Blog | Cloud Provider | RSS | `https://aws.amazon.com/blogs/machine-learning/feed/` |
| 28 | Azure AI Blog | Cloud Provider | RSS | `https://techcommunity.microsoft.com/t5/ai-azure-ai-services-blog/bg-p/Azure-AI-Services-blog/rss` |
| 29 | Google Cloud AI Blog | Cloud Provider | RSS | `https://cloud.google.com/feeds/cloud-blog.xml` — filter items containing AI/ML keywords |
| 30 | TechCrunch AI | News | RSS | `https://techcrunch.com/category/artificial-intelligence/feed/` |
| 31 | VentureBeat AI | News | RSS | `https://venturebeat.com/category/ai/feed/` |
| 32 | Anthropic Economic Index | Usage Metrics | CSV/Web | `https://www.anthropic.com/research/economic-index-geography` — first-party API usage data: task categories, automation vs augmentation split, geographic distribution. Check for downloadable datasets. |

### Fetch Logic for New Source Types

**SEC EDGAR (source 21):**
- Use `requests` with `User-Agent` header (SEC requires identifying your app)
- Parse JSON response, extract filing URLs, titles, company names, dates
- For each filing, store the search snippet (not full filing text — too large)
- Deduplicate by filing accession number

**Government procurement APIs (sources 23-25):**
- These return structured JSON with contract details
- Extract: agency/department, vendor name, contract value, description, date
- Filter for AI-relevant contracts using keyword matching on descriptions
- SAM.gov requires a free API key — store as `SAM_GOV_API_KEY` env variable
- TED EU API is unauthenticated

**Cloudflare Radar (source 26):**
- Requires Cloudflare API token with Radar read permissions
- Returns time-series JSON data
- Store as structured data, not text content
- Fetch weekly, not daily (data doesn't change fast enough)

**Cloud provider blogs and news (sources 27-31):**
- Standard RSS fetch using existing `rss_fetcher.py`
- These produce many items — filter for AI/ML relevance using keyword matching on title + summary before storing
- Keywords: "AI", "artificial intelligence", "machine learning", "LLM", "generative AI", "foundation model", "Copilot", "Bedrock", "Vertex AI", "Claude", "GPT", "Gemini"

**Anthropic Economic Index (source 32):**
- Check the page for downloadable CSV/JSON files
- If structured data is available, download and parse
- If not, scrape the key metrics from the page
- Update monthly (this is not a daily source)

---

## 3. Database Schema Changes

### New Migration File

Create `src/db/migrations/002_diffusion_track.sql`:

```sql
-- Add track column to sources table to distinguish cognitive vs diffusion
ALTER TABLE sources ADD COLUMN IF NOT EXISTS track VARCHAR(20) DEFAULT 'cognitive';

-- Update existing sources to be explicitly cognitive
UPDATE sources SET track = 'cognitive' WHERE track IS NULL;

-- Add track column to wave1_outputs for filtering
ALTER TABLE wave1_outputs ADD COLUMN IF NOT EXISTS track VARCHAR(20) DEFAULT 'cognitive';

-- Add track column to reports for filtering
ALTER TABLE reports ADD COLUMN IF NOT EXISTS track VARCHAR(20) DEFAULT 'cognitive';

-- Create diffusion-specific wave1 outputs table
-- (Alternative: reuse wave1_outputs with track column — choose based on existing implementation)
CREATE TABLE IF NOT EXISTS diffusion_wave1_outputs (
    id SERIAL PRIMARY KEY,
    report_cycle_id VARCHAR(50) NOT NULL,
    fetched_item_id INTEGER REFERENCES fetched_items(id),
    source_weight INTEGER CHECK (source_weight BETWEEN 1 AND 5),
    weight_justification TEXT,
    findings JSONB NOT NULL,  -- array of {finding, cascade_order, player_or_domain, evidence, confidence}
    model_used VARCHAR(100),
    tokens_used INTEGER,
    cost_usd NUMERIC(10,6),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create diffusion reports table
CREATE TABLE IF NOT EXISTS diffusion_reports (
    id SERIAL PRIMARY KEY,
    report_cycle_id VARCHAR(50) UNIQUE NOT NULL,
    report_tree JSONB NOT NULL,  -- three-layer tree structure for diffusion
    model_used VARCHAR(100),
    total_cost_usd NUMERIC(10,4),
    items_analysed INTEGER,
    sources_covered INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index new tables
CREATE INDEX IF NOT EXISTS idx_diffusion_wave1_cycle ON diffusion_wave1_outputs(report_cycle_id);
CREATE INDEX IF NOT EXISTS idx_diffusion_reports_cycle ON diffusion_reports(report_cycle_id);
CREATE INDEX IF NOT EXISTS idx_sources_track ON sources(track);
```

### Seed New Sources

Create or extend `src/db/seed_sources.py` to insert the 12 new sources with `track = 'diffusion'`. Do not re-insert existing cognitive sources. Use `INSERT ... ON CONFLICT DO NOTHING` to make it idempotent.

---

## 4. Diffusion Processing Pipeline

### Overview

The diffusion processing pipeline mirrors the cognitive pipeline's two-wave architecture but uses different analytical frameworks and produces different outputs.

**Trigger:** A separate report generation job, running on the same schedule as cognitive (every N days, default 3) but as a separate workflow.

**Item selection:** For each report cycle, the diffusion pipeline analyses:
1. All unprocessed `fetched_items` from diffusion-track sources (IDs 21-32)
2. All unprocessed `fetched_items` from shared sources (IDs 6-10, 16-18) that have NOT yet been analysed by the diffusion pipeline

To track which items have been processed by the diffusion pipeline specifically, either:
- Add a `diffusion_processed BOOLEAN DEFAULT false` column to `fetched_items`, OR
- Track processed item IDs in the `diffusion_wave1_outputs` table and exclude items already present

Choose whichever approach is cleaner given the existing implementation.

### Wave 1: Source-Level Diffusion Analysis

**Input per API call:**
- System prompt: The AI Diffusion Evaluation Framework (see Section 6 — embed the full framework text)
- User prompt: Content from one source or a batch of related items from one source
- Instructions: Extract diffusion-relevant findings, map to cascade order and player/domain, assign source weight

**Source weight guidelines for diffusion (embedded in the Wave 1 system prompt):**

| Weight | Description | Examples |
|--------|-------------|---------|
| 5 | Verified financial data, government procurement records, audited filings | SEC 10-K/10-Q with AI revenue breakdowns, SAM.gov contract awards, Epoch AI revenue CSV with cited sources |
| 4 | Primary announcements from first-order players | AI lab partnership announcements, government AI policy announcements, cloud provider AI service launches |
| 3 | Expert analysis of AI business/adoption dynamics | Newsletter analysis of AI market dynamics, credentialed industry analyst commentary |
| 2 | Aggregated usage metrics and market reports | Cloudflare Radar traffic data, Ramp AI Index reports, EU procurement aggregates |
| 1 | Unverified claims, speculation, promotional content | Vendor marketing materials, unverified revenue claims, social media speculation |

**Output format per call (JSON):**
```json
{
  "source_id": 21,
  "source_name": "SEC EDGAR",
  "source_weight": 5,
  "weight_justification": "Audited regulatory filing; legally verified financial data",
  "findings": [
    {
      "finding": "Accenture reported $3B in generative AI bookings in Q4 2025, up 200% YoY",
      "cascade_order": 2,
      "cascade_category": "enterprise_adoption",
      "player_or_domain": "Management consulting",
      "evidence_type": "financial_disclosure",
      "confidence": "high",
      "q1_q2_q3_relevance": "Q3",
      "notes": "Indicates rapid enterprise consulting adoption; directly impacts consulting workforce"
    }
  ]
}
```

**Field definitions:**
- `cascade_order`: 1 (first-order player action), 2 (major consumer/institutional), 3 (downstream to people), 0 (direct channel — labs to individuals)
- `cascade_category`: One of: `lab_strategy`, `government_action`, `cloud_infrastructure`, `platform_decision`, `capital_flow`, `enterprise_adoption`, `defense_procurement`, `direct_to_individual`, `workforce_impact`, `consumer_impact`, `supply_constraint`, `feedback_loop`
- `q1_q2_q3_relevance`: Which of the three output questions this finding helps answer: "Q1" (current AI capabilities per task), "Q2" (near-future capabilities), "Q3" (industry absorption timeline), or "Q1,Q2" etc. for multiple.

**Batching logic:** Same as cognitive — group by source, batch 10-15 items per call, use Batch API.

### Wave 2: Diffusion Synthesis and Report Generation

**Input:**
- System prompt: The AI Diffusion Evaluation Framework (same as Wave 1)
- User prompt: All Wave 1 findings aggregated into an intermediate document
- **Cognitive track context:** Before constructing the Wave 2 API call, query the `reports` table for the latest cognitive track report (`SELECT report_tree, scenario_assessment FROM reports WHERE track = 'cognitive' ORDER BY created_at DESC LIMIT 1`). Extract the executive summary, scenario assessment, and all five criteria satisfaction percentages from the `report_tree` JSON. Include this as a clearly labelled section at the top of the user prompt, formatted as:

```
--- COGNITIVE TRACK CONTEXT (from latest cognitive report, dated {date}) ---
Scenario Assessment: {scenario_assessment}
Criterion 1 (Intellectual Scope): {satisfaction_pct}%
Criterion 2 (Causal World Model): {satisfaction_pct}%
Criterion 3 (Goal Decomposition): {satisfaction_pct}%
Criterion 4 (Self-Directed Learning): {satisfaction_pct}%
Criterion 5 (Meta-Reasoning): {satisfaction_pct}%
Executive Summary: {executive_summary_text}
--- END COGNITIVE TRACK CONTEXT ---
```

If no cognitive report exists yet in the database, the Context Integrity instruction in the framework will cause the LLM to return a MISSING CONTEXT note rather than hallucinate. This is the intended behaviour — the diffusion report cannot fully answer Q2 without the cognitive track assessment.

- Instructions: Produce the diffusion report tree (see Section 5)

**If the intermediate document exceeds context window:**
- Split by cascade order: one Wave 2 call per cascade order (first-order, direct channel, second-order, third-order)
- One final Wave 2 call takes all cascade assessments and produces the top-level synthesis

**Output:** The complete diffusion report tree JSON (see Section 5)

**After Wave 2 completes:**
- Save to `diffusion_reports` table
- Generate static HTML from the report tree
- Push to GitHub Pages (as a separate page, e.g., `diffusion/index.html`)
- Send Telegram notification

---

## 5. Diffusion Report Tree Structure

### Three-Layer Design

Same node structure as cognitive reports:
```json
{
  "id": "section_id",
  "title": "Section title",
  "summary": "2-3 sentence verdict",
  "children": [...]
}
```

### Top-Level Structure (Layer 1)

1. **Executive Summary** — overall assessment of AI diffusion state. Key disruptions observed or emerging. 3-4 sentences.
2. **First-Order Player Moves** — what are AI labs, governments, cloud providers, platform owners, open-source platforms, and capital allocators doing? What do their actions signal about diffusion trajectory?
3. **Direct Channel: Labs → Individuals** — how are AI capabilities reaching individuals directly? What patterns are being disrupted? Key case: AI substituting for institutions (education, professional services).
4. **Institutional Channel: Major Consumers** — which enterprises, defense organizations, and other institutional consumers are adopting AI? What is the observed impact on their output?
5. **Downstream Impact: Reaching People** — where institutional AI adoption is changing what people experience as consumers or workers.
6. **Three Questions Assessment:**
   - **Q1 — What can AI do for tasks today?** — summary of current capability-to-task mapping based on observed adoption patterns.
   - **Q2 — What can AI do in the near future?** — derived from cognitive track scenario assessment + task classification.
   - **Q3 — When will industries absorb this?** — only for industries where cascade evidence exists. Rough staging: fast/moderate/slow adopter.
7. **Supply-Side Constraints and Feedback Loops** — observed bottlenecks and dynamics that are accelerating or braking diffusion.

Each top-level node contains 2-5 Layer 2 evidence clusters. Each evidence cluster contains 2-4 Layer 3 detailed evidence items with references.

### HTML Rendering

Generate a separate HTML page at `output/diffusion/index.html` using the same expandable tree template as the cognitive report. Include a link from each report to the other (cognitive ↔ diffusion).

The main `output/index.html` should serve as a landing page linking to both the cognitive and diffusion reports if both exist.

---

## 6. The AI Diffusion Evaluation Framework

This is the analytical framework that drives all diffusion LLM analysis. It must be included in full as the system prompt for both Wave 1 and Wave 2 API calls.

**Store this at `framework/ai_diffusion_framework.md` in the repository.** Claude Code must read this file and use its contents as the system prompt. Do NOT summarise or truncate it.

**Copy the content below into that file:**

---

BEGIN FRAMEWORK DOCUMENT

# AI Diffusion Evaluation Framework

## Your Role

You are an analyst tracking how AI capabilities propagate through society. Your job is to evaluate incoming information against this framework and extract structured findings about AI diffusion — who is adopting AI, through what channels, at what scale, and with what impact on societal patterns.

## Critical Instruction: Context Integrity

Before producing any analysis, verify that all context required by this framework is available in this conversation. If the framework references external information, assessments, or outputs from other systems (e.g., cognitive track scenarios, scenario progression timelines, capability assessments) that are NOT present in the provided context, do NOT attempt to infer, reconstruct, or approximate that information from your training data. Instead, return ONLY a response in this format:

```
MISSING CONTEXT: [description of what is needed and why]
```

Do not produce any analytical output alongside this note. The purpose is to surface gaps for the system operator to fix, not to produce a partial or potentially hallucinated analysis. Only proceed with full analysis when all referenced context is available.

## Objective

Predict disruptions in societal patterns that are sufficiently significant and relevant, caused by AI capabilities propagating through society. Prediction horizons: present, 2 years, 5 years.

This framework captures *diffusion* — how capabilities reach people and reshape patterns — not capability development itself. Capability assessments are imported from the cognitive AI track.

## The Cascade: How AI Capabilities Flow Through Society

### First-Order Players

A first-order player is any actor who can singlehandedly influence more than 5% of AI diffusion in society — positively or negatively.

| Player | Role | What to Track |
|--------|------|---------------|
| **AI Labs** (OpenAI, Google DeepMind, Anthropic, Meta AI, DeepSeek, Mistral, xAI) | Create frontier capabilities | Release strategy (open vs closed), pricing decisions, API access terms, partnership announcements, customer milestones, revenue growth |
| **Governments** (US, China, EU, UK) | Regulate, fund, restrict, mandate | AI policy announcements, export controls, procurement contracts, funding mandates, regulatory actions (EU AI Act enforcement, US executive orders) |
| **Cloud Providers** (AWS, Azure, GCP) | Control distribution infrastructure | AI service launches, pricing changes, regional availability, model marketplace decisions, enterprise customer announcements |
| **Mobile Platform Owners** (Apple, Google) | Gate AI on billions of devices | OS-level AI integration, AI feature announcements, app store AI policies |
| **Open-Source AI Distribution Platforms** (HuggingFace, GitHub, Ollama, Together AI) | Distribute open-weight models | Model hosting decisions, platform policy changes, download/usage metrics |
| **Capital Allocators** (VCs, sovereign wealth funds) | Fund or defund AI | Funding rounds, investment trends, valuation signals, capital concentration patterns |

**Vertically integrated players:** Google spans lab + cloud + mobile + chips. Microsoft spans cloud + lab partner. Track cross-role leverage as a feedback loop.

**NVIDIA/chip ecosystem:** Treat as static background condition. Tripwire: if NVIDIA moves to control which models run on their hardware, flag for re-evaluation as first-order player.

For each first-order player, assess: **motivations** (explicitly stated or inferred from actions), **recent actions**, and **what their actions signal about diffusion trajectory**.

### Direct Channel: Labs → Individuals

AI labs' pricing tiers, capability levels, and access terms create a direct diffusion path to individuals — bypassing institutions. This includes both free and paid users.

Key pattern: disruption flows through this channel when AI capability available to individuals is **sufficient to break an existing pattern** in their lives (freelance market collapse, education assessment disruption, self-learning replacing paid courses).

Key case: **AI substituting for institutions.** AI may make certain institutions *optional* — e.g., individuals acquiring expert knowledge without a university degree. This bypasses the institutional channel entirely.

### Second Order: Major Institutional Consumers

Who is paying AI labs for capabilities? What is their output? How does AI change the quality and quantity of that output?

Track: enterprise AI adoption deals, defense/intelligence procurement, institutional licensing (e.g., university ChatGPT licenses), enterprise software platforms embedding AI (Salesforce, Microsoft/Office, SAP, Adobe).

### Third Order: Downstream to People

Trace institutional AI adoption to its impact on individuals — as workers (job displacement, role transformation, skill requirements) and as consumers (cheaper services, new access for previously priced-out populations, transformed service experience, new risks from AI limitations).

### Disruption Threshold

At each cascade level, distinguish between:
- **Incremental efficiency gains** — not the focus (ignore or deprioritise)
- **Structural pattern disruption** — the target of prediction (highlight and analyse)

A structural pattern disruption occurs when individual AI adoption aggregates into a change in societal patterns — e.g., a job category contracting, an industry restructuring, an institution becoming optional.

## Three Output Questions

Every finding should be tagged with which question(s) it helps answer:

**Q1: What can AI do for tasks today?** (High reliability) What current AI capabilities are being actively used for which tasks? Based on observed adoption, not theoretical capability.

**Q2: What can AI do for tasks in the near future?** (Moderate reliability) Based on cognitive track scenario progression, what tasks will become automatable as capabilities advance? Map task nature to scenario level:
- Category 1 (routine cognitive + short horizon) → automatable at Scenario A (now)
- Category 2 (pattern-recombination + medium horizon) → automatable at Scenario B
- Category 3 (contextual judgment + long horizon) → automatable at Scenario B→C transition
- Category 4 (novel problem-solving + open-ended horizon) → requires Scenario D or E

**Q3: When will specific industries absorb this?** (Lower reliability) For industries where cascade evidence exists, estimate rough staging: fast adopter, moderate, or slow. Base this on the dominant adoption forces for that industry.

## What Makes a Finding Worth Extracting

Extract a finding when the information:
1. Reveals a first-order player's action, strategy, or motivation
2. Shows measurable AI adoption by an institutional consumer (contract value, user count, revenue impact)
3. Indicates a structural pattern disruption (not incremental improvement)
4. Provides evidence about the rate of diffusion (accelerating or braking forces)
5. Reveals supply-side constraints affecting diffusion
6. Shows feedback loops (e.g., public backlash → regulation → lab constraints)

Do NOT extract:
- Promotional content without verifiable claims
- Speculation without evidence
- Incremental product updates without strategic significance
- Technical capability benchmarks (these belong in the cognitive track, not diffusion)

## Source Weight Assessment

When evaluating a source, assign a weight 1-5:

| Weight | Criteria |
|--------|----------|
| 5 | Legally verified data (SEC filings, government procurement records), audited financials, peer-reviewed research with transparent methodology |
| 4 | Primary announcements from first-order players, official government policy documents |
| 3 | Expert analysis from credentialed industry analysts, established newsletter commentary |
| 2 | Aggregated usage metrics, market reports, survey data |
| 1 | Unverified claims, vendor marketing, social media speculation |

Always justify the weight assignment.

END FRAMEWORK DOCUMENT

---

## 7. Scheduling (GitHub Actions)

### Workflow 3: Diffusion Fetch (extends existing daily fetch)

The simplest approach: modify the existing `fetch.yml` workflow to also fetch diffusion sources in the same daily run. The `src/fetch/main.py` orchestrator should fetch ALL active sources regardless of track.

If modifying the existing workflow is too invasive, create a separate workflow:

```yaml
name: Daily Fetch (Diffusion Sources)
on:
  schedule:
    - cron: '0 7 * * *'  # 07:00 UTC daily (1 hour after cognitive fetch)
  workflow_dispatch:

jobs:
  fetch:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: python src/fetch/main.py --track diffusion
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          SAM_GOV_API_KEY: ${{ secrets.SAM_GOV_API_KEY }}
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
```

**Preferred approach:** Extend the existing fetch to handle all sources in one run. Add a `--track` CLI argument to `main.py` that allows fetching only cognitive, only diffusion, or all sources. Default: all.

### Workflow 4: Diffusion Report Generation

```yaml
name: Generate Diffusion Report
on:
  schedule:
    - cron: '0 10 */3 * *'  # 10:00 UTC every 3 days (2 hours after cognitive report)
  workflow_dispatch:

jobs:
  process:
    runs-on: ubuntu-latest
    timeout-minutes: 120
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: python src/process/diffusion_main.py
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          LLM_PROVIDER: openai
          LLM_MODEL: gpt-4o
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
      - run: python src/report/generate_diffusion_html.py
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./output
```

---

## 8. Telegram Notifications (Diffusion-specific)

Add these notification types alongside existing ones. Prefix diffusion notifications with a distinct emoji to distinguish from cognitive track.

**Diffusion fetch summary:**
```
🌐 Diffusion fetch: {date} {time} UTC
✅ {n_success}/{n_total} sources OK
⚠️ {source}: {warning}
❌ {source}: {error}
New items: {total} ({breakdown})
```

**Diffusion high-signal update:**
```
🌐🔔 High-signal diffusion update
Source: {name} (weight {n})
Cascade order: {order}
Title: "{title}"
```
Trigger when a weight-4 or weight-5 diffusion source publishes content that indicates a major first-order player move or significant institutional adoption deal.

**Diffusion report generated:**
```
🌐📊 Diffusion report: {date}
Sources processed: {n_items} items from {n_sources} sources
Findings extracted: {n_findings}
By cascade order: 1st:{n} | Direct:{n} | 2nd:{n} | 3rd:{n}
Q1 findings: {n} | Q2: {n} | Q3: {n}
Batch API cost: ${cost}
Report URL: {url}
```

---

## 9. Project Structure (New Files Only)

```
agi-tracker/
├── .github/
│   └── workflows/
│       ├── fetch.yml                         # MODIFY: add diffusion sources
│       ├── report.yml                        # EXISTING: cognitive report (do not modify)
│       └── diffusion_report.yml              # NEW: diffusion report generation
├── framework/
│   ├── agi_evaluation_framework.md           # EXISTING: cognitive (do not modify)
│   └── ai_diffusion_framework.md             # NEW: diffusion evaluation framework
├── src/
│   ├── fetch/
│   │   ├── main.py                           # MODIFY: add --track argument, register new fetchers
│   │   ├── sec_edgar_fetcher.py              # NEW: SEC EDGAR API fetcher
│   │   ├── gov_procurement_fetcher.py        # NEW: SAM.gov, USAspending, TED EU
│   │   ├── cloudflare_radar_fetcher.py       # NEW: Cloudflare Radar AI insights
│   │   ├── csv_fetcher.py                    # MODIFY: add Epoch AI revenue CSV
│   │   └── (existing fetchers unchanged)
│   ├── process/
│   │   ├── main.py                           # EXISTING: cognitive processing (do not modify)
│   │   ├── diffusion_main.py                 # NEW: orchestrates diffusion Wave 1 → Wave 2
│   │   ├── diffusion_wave1.py                # NEW: diffusion-specific Wave 1 logic
│   │   ├── diffusion_wave2.py                # NEW: diffusion-specific Wave 2 logic
│   │   ├── diffusion_prompts.py              # NEW: diffusion prompt templates
│   │   ├── prompts.py                        # EXISTING: cognitive prompts (do not modify)
│   │   ├── wave1.py                          # EXISTING: cognitive Wave 1 (do not modify)
│   │   └── wave2.py                          # EXISTING: cognitive Wave 2 (do not modify)
│   ├── report/
│   │   ├── generate_html.py                  # EXISTING: cognitive report (do not modify)
│   │   ├── generate_diffusion_html.py        # NEW: diffusion report HTML generation
│   │   ├── template.html                     # EXISTING: cognitive template
│   │   └── diffusion_template.html           # NEW: diffusion report template
│   ├── db/
│   │   └── migrations/
│   │       ├── 001_initial_schema.sql        # EXISTING (do not modify)
│   │       └── 002_diffusion_track.sql       # NEW: diffusion schema additions
│   └── (other existing files unchanged)
├── output/
│   ├── index.html                            # MODIFY: make landing page linking to both reports
│   └── diffusion/
│       └── index.html                        # NEW: diffusion report output
└── SPEC_Diffusion.md                         # This file
```

---

## 10. Environment Variables (New)

Add these to `.env.example` and GitHub Actions secrets:

```
# Diffusion-specific source auth
SAM_GOV_API_KEY=...             # Free API key from sam.gov
CLOUDFLARE_API_TOKEN=...        # Cloudflare API token with Radar read permissions

# Diffusion-specific configuration
DIFFUSION_REPORT_INTERVAL_DAYS=3
```

All other variables (DATABASE_URL, OPENAI_API_KEY, TELEGRAM_*, LLM_PROVIDER, LLM_MODEL) are shared with the cognitive track.

---

## 11. TECHNICAL.md Updates

Add the following sections to the existing TECHNICAL.md:

1. **Diffusion track overview** — relationship to cognitive track, shared vs separate components
2. **Diffusion source registry** — every new source with fetch method, URL, auth, rate limits, quirks
3. **Diffusion schema** — the actual migration SQL that was executed
4. **Diffusion prompt architecture** — the prompt templates used for Wave 1 and Wave 2
5. **Diffusion report tree schema** — JSON schema with example
6. **New GitHub Actions workflows** — what triggers them, what secrets they need
7. **Diffusion notification formats** — actual message templates
8. **Discrepancies found** — any differences between this spec and what was actually implemented

---

## 12. Implementation Notes

### Shared Fetch Layer Design

The key principle: **fetch once, analyse twice.** Sources relevant to both tracks get fetched once (by the daily fetch job) and stored once (in `fetched_items`). The cognitive pipeline and diffusion pipeline each independently query `fetched_items` for their relevant sources and produce separate analyses.

This means:
- The `sources` table has a `track` column, but some sources are relevant to both tracks
- The fetch orchestrator fetches ALL active sources regardless of track
- Each processing pipeline selects items by source IDs relevant to its track
- A single `fetched_item` can be processed by both pipelines independently

### Handling Shared Sources

For sources that are relevant to both tracks (lab blogs, Epoch AI, newsletters), the diffusion pipeline must:
1. Check which items from shared sources have NOT been processed by the diffusion pipeline yet
2. Process them with diffusion-specific prompts
3. Mark them as diffusion-processed

Use a separate tracking mechanism (e.g., entries in `diffusion_wave1_outputs`) rather than modifying the `processed` flag on `fetched_items` (which is used by the cognitive pipeline).

### Error Handling

Same principles as cognitive track:
- Every fetch source wrapped in try/catch
- Log errors to `fetch_logs`
- Exponential backoff for transient failures
- Flag sources that fail 3 consecutive cycles

### Rate Limiting

- SEC EDGAR: 10 req/sec (generous, but be polite)
- SAM.gov: 1,000 req/day with API key
- USAspending: no documented limit, use 1 req/sec
- TED EU: no documented limit, use 1 req/sec
- Cloudflare Radar: standard API rate limits (1,200 req/5min for free tier)
- All RSS feeds: same 1-second delay as cognitive track

### Testing

- Write integration tests for each new fetcher
- Write a test verifying diffusion Wave 1 prompt produces valid JSON
- Write a test verifying diffusion HTML generator produces valid output
- Tests should be runnable alongside existing cognitive tests without interference

---

## 13. Getting Started Checklist (For the Developer)

After Claude Code finishes implementation:

1. [ ] Review the `diffusion-track` branch diff against `main`
2. [ ] Run the new migration: `psql $DATABASE_URL -f src/db/migrations/002_diffusion_track.sql`
3. [ ] Seed new sources: `python src/db/seed_sources.py` (should be idempotent)
4. [ ] Get a SAM.gov API key at sam.gov (free registration)
5. [ ] Get a Cloudflare API token (free tier) with Radar read permissions
6. [ ] Add new secrets to GitHub Actions: `SAM_GOV_API_KEY`, `CLOUDFLARE_API_TOKEN`
7. [ ] Copy the diffusion framework into `framework/ai_diffusion_framework.md`
8. [ ] Test fetch locally: `python src/fetch/main.py --track diffusion`
9. [ ] Test processing locally: `python src/process/diffusion_main.py`
10. [ ] Verify HTML output at `output/diffusion/index.html`
11. [ ] Merge the branch into main
12. [ ] Enable the new GitHub Actions workflow
