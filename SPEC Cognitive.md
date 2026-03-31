# AGI Capability Tracker — System Specification

## What This Document Is

This is the complete specification for building an automated system that tracks progress toward Artificial General Intelligence (AGI) on the cognitive capabilities track. Claude Code should implement everything described here. Where implementation details are unspecified, make reasonable decisions and document them in TECHNICAL.md.

---

## 1. System Overview

### Purpose
Programmatically fetch information from 20 curated sources about AI capabilities, analyse it against a rigorous five-criteria AGI evaluation framework, and produce a structured report assessing where current AI systems stand.

### Architecture
Three layers: **Fetch** → **Store** → **Process**

- **Fetch:** Daily scheduled jobs pull new content from 20 sources. Results are stored in a database. A Telegram notification summarises each fetch cycle.
- **Store:** PostgreSQL (Neon) holds raw fetched content, intermediate LLM analysis, and final reports.
- **Process:** Every N days (default: 3), a two-wave LLM pipeline analyses fetched content and produces a tree-structured report. Wave 1 extracts and weights claims from each source. Wave 2 synthesises weighted claims into the final report.

### Deployment
- **Compute:** GitHub Actions (scheduled workflows for fetch and processing)
- **Storage:** Neon PostgreSQL (free tier)
- **Public access:** GitHub Pages (static HTML report with expandable sections)
- **Notifications:** Telegram Bot API

### LLM Provider
- **Default:** OpenAI GPT-4o via Batch API
- **Alternatives:** Anthropic Claude, Google Gemini (abstracted behind a provider interface for future swapping)
- Start with OpenAI as the only implemented provider. Structure the code so adding Anthropic and Gemini later requires implementing a single adapter class per provider, not rewriting the pipeline.

---

## 2. Data Sources (20 for v1)

Each source has an ID, a fetch method, and a category. Implement fetch logic per source type.

### Source List

| ID | Source | Category | Fetch Method | URL / Endpoint |
|----|--------|----------|-------------|----------------|
| 1 | arXiv cs.AI | Papers | RSS | `https://arxiv.org/rss/cs.AI` |
| 2 | arXiv cs.LG | Papers | RSS | `https://arxiv.org/rss/cs.LG` |
| 3 | arXiv cs.CL | Papers | RSS | `https://arxiv.org/rss/cs.CL` |
| 4 | Semantic Scholar | Papers | REST API | `https://api.semanticscholar.org/graph/v1/paper/search` — search for AI reasoning, world models, causal reasoning, self-directed learning. Free API key via x-api-key header. Rate limit: 1 RPS authenticated. |
| 5 | OpenReview (ICLR/NeurIPS/ICML) | Papers | Python SDK | `pip install openreview-py`. Use `client.get_all_notes()` for latest submissions. Requires OpenReview account (username/password). |
| 6 | Epoch AI datasets | Quantitative | CSV download | `https://epoch.ai/data/ai-models` — download CSV. Also `https://epoch.ai/benchmarks` for benchmark aggregation. CC-BY license. |
| 7 | OpenAI blog | Lab blog | RSS | `https://openai.com/news/rss.xml` |
| 8 | Google DeepMind blog | Lab blog | RSS | `https://deepmind.google/blog/rss.xml` |
| 9 | Anthropic research | Lab blog | RSS (scraped) | Use Olshansk scraper feeds: `https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml` and `feed_anthropic_news.xml` |
| 10 | Meta AI (FAIR) | Lab blog | RSS | `https://research.facebook.com/feed/` |
| 11 | DeepSeek releases | Lab releases | GitHub API + HuggingFace API | GitHub: `https://api.github.com/orgs/deepseek-ai/repos` (sort by updated). HuggingFace: `https://huggingface.co/api/models?author=deepseek-ai&sort=lastModified` |
| 12 | ARC-AGI leaderboard | Benchmark | Web scrape or API | `https://arcprize.org/leaderboard` — check for structured data endpoint first, fall back to scraping. |
| 13 | Epoch AI Benchmarking Hub | Benchmark | CSV download | `https://epoch.ai/benchmarks` — download aggregated benchmark data. |
| 14 | HuggingFace Open LLM Leaderboard | Benchmark | HuggingFace Datasets API | `from datasets import load_dataset; ds = load_dataset("open-llm-leaderboard/contents")` |
| 15 | SWE-bench | Benchmark | GitHub | Leaderboard JSON at `https://github.com/SWE-bench/swe-bench.github.io` |
| 16 | Import AI newsletter | Newsletter | RSS | `https://importai.substack.com/feed` |
| 17 | Interconnects newsletter | Newsletter | RSS | `https://www.interconnects.ai/feed` |
| 18 | Zvi Mowshowitz AI roundup | Newsletter | RSS | `https://thezvi.substack.com/feed` |
| 19 | UK AI Safety Institute | Institutional | Web fetch | `https://www.aisi.gov.uk/research` — fetch publication list, check for new reports. |
| 20 | LessWrong | Community | GraphQL API | Endpoint: `https://www.lesswrong.com/graphql`. Query: `{ posts(input: { terms: { view: "new", limit: 50 } }) { results { _id, title, postedAt, baseScore, commentCount, url } } }`. No auth needed. Filter by baseScore > 30 for quality. |

### Fetch Logic by Type

**RSS feeds (sources 1-3, 7-10, 16-18):**
- Use `feedparser` Python library
- Extract: title, link, published date, summary/description
- Deduplicate by URL against existing database entries

**REST APIs (sources 4, 11, 14):**
- Implement per-source with appropriate auth headers
- Handle pagination where applicable
- Respect rate limits (implement backoff)

**CSV downloads (sources 6, 13):**
- Download file, parse with pandas
- Compare against previous download to identify new/changed rows
- Store the diff, not the entire file each time

**Python SDK (source 5):**
- OpenReview requires account credentials stored as environment variables
- Fetch latest submissions from top venues

**Web scrape / GitHub (sources 12, 15, 19):**
- Use `requests` + `beautifulsoup4` for HTML
- GitHub API for structured JSON
- Be conservative with scraping — add delays, respect robots.txt

**GraphQL (source 20):**
- POST request with JSON body to GraphQL endpoint
- No auth required for reads

---

## 3. Database Schema (Neon PostgreSQL)

### Tables

```sql
CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    fetch_method VARCHAR(50) NOT NULL,
    url TEXT,
    weight_default INTEGER DEFAULT 3 CHECK (weight_default BETWEEN 1 AND 5),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE fetched_items (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES sources(id),
    external_id VARCHAR(500),  -- URL, DOI, or other unique identifier from source
    title TEXT,
    content TEXT,  -- full text, abstract, or summary
    url TEXT,
    published_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT NOW(),
    fetch_cycle_id VARCHAR(50),  -- groups items from same fetch run
    processed BOOLEAN DEFAULT false,
    UNIQUE(source_id, external_id)
);

CREATE TABLE wave1_outputs (
    id SERIAL PRIMARY KEY,
    report_cycle_id VARCHAR(50) NOT NULL,  -- groups outputs for same report
    fetched_item_id INTEGER REFERENCES fetched_items(id),
    source_weight INTEGER CHECK (source_weight BETWEEN 1 AND 5),
    weight_justification TEXT,
    claims JSONB NOT NULL,  -- array of {claim, criterion, evidence, confidence}
    model_used VARCHAR(100),
    tokens_used INTEGER,
    cost_usd NUMERIC(10,6),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    report_cycle_id VARCHAR(50) UNIQUE NOT NULL,
    report_tree JSONB NOT NULL,  -- the full three-layer tree structure
    scenario_assessment VARCHAR(10),  -- e.g., "A", "A→B", "B"
    model_used VARCHAR(100),
    total_cost_usd NUMERIC(10,4),
    items_analysed INTEGER,
    sources_covered INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE fetch_logs (
    id SERIAL PRIMARY KEY,
    fetch_cycle_id VARCHAR(50) NOT NULL,
    source_id INTEGER REFERENCES sources(id),
    status VARCHAR(20) NOT NULL,  -- 'success', 'warning', 'error'
    items_found INTEGER DEFAULT 0,
    error_message TEXT,
    duration_seconds NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Indexing
- Index `fetched_items` on `(source_id, published_at)` and `(fetch_cycle_id)`
- Index `wave1_outputs` on `(report_cycle_id)`
- Index `fetched_items` on `(processed, fetched_at)` for the processing pipeline to find unprocessed items

---

## 4. Processing Pipeline

### Wave 1: Source-Level Analysis

**Trigger:** Report generation job (every N days, default 3)

**Input per API call:**
- System prompt: The AGI evaluation framework (see Section 6 — embed the full framework text)
- User prompt: Content from one source or a batch of related items from one source
- Instructions: Extract claims, map to criteria, assign source weight

**Source weight guidelines (embedded in the Wave 1 system prompt):**

| Weight | Description | Examples |
|--------|-------------|---------|
| 5 | Peer-reviewed benchmark with transparent methodology, independent research org | ARC-AGI results, Epoch AI quantitative data, peer-reviewed papers |
| 4 | Major lab primary publication with reproducible claims | DeepMind blog announcing AlphaProof, OpenAI system cards |
| 3 | Expert analysis by credentialed researcher | Import AI, Interconnects, Zvi's roundup |
| 2 | Institutional assessment or curated leaderboard | UK AISI report, HuggingFace leaderboard, SWE-bench |
| 1 | Community discussion or unverified claims | LessWrong posts, trending repos |

**Output format per call (JSON):**
```json
{
  "source_id": 7,
  "source_name": "OpenAI blog",
  "source_weight": 4,
  "weight_justification": "Primary lab publication; claims are first-party but self-interested",
  "claims": [
    {
      "claim": "GPT-5.2 scores 92.4% on GPQA Diamond",
      "criterion": 1,
      "evidence_type": "benchmark_score",
      "confidence": "high",
      "notes": "Self-reported; awaiting independent verification"
    }
  ]
}
```

**Batching logic:**
- Group fetched items by source
- For sources with many items (arXiv may have 50+ papers per cycle), batch into groups of 10-15 items per API call
- For sources with few items (a single blog post), one API call per source
- Use OpenAI Batch API for all Wave 1 calls

**After Wave 1 completes:**
- Save all outputs to `wave1_outputs` table
- Mark processed `fetched_items` as `processed = true`
- Aggregate all claims into a single intermediate JSON document for Wave 2

### Wave 2: Synthesis and Report Generation

**Input:**
- System prompt: The AGI evaluation framework (same as Wave 1)
- User prompt: The aggregated intermediate document from Wave 1 (all claims, weights, and justifications)
- Instructions: Produce the three-layer report tree (see Section 5)

**If the intermediate document exceeds context window:**
- Split by criterion: one Wave 2 call per criterion (5 calls), each producing that criterion's branch of the tree
- One final Wave 2 call takes all 5 criterion assessments and produces the top-level synthesis + scenario assessment

**Output:** The complete report tree JSON (see Section 5)

**After Wave 2 completes:**
- Save to `reports` table
- Generate static HTML from the report tree
- Push to GitHub Pages
- Send Telegram notification

### API Call Implementation

**OpenAI Batch API specifics:**
- Endpoint: `POST https://api.openai.com/v1/batches`
- Create JSONL file with all requests
- Upload as a file, create batch, poll for completion
- Batch API offers 50% cost reduction and higher rate limits
- 24-hour completion window (usually much faster)

**Provider abstraction:**
```python
class LLMProvider:
    def submit_batch(self, requests: list[dict]) -> str:  # returns batch_id
    def check_batch_status(self, batch_id: str) -> str:  # returns status
    def get_batch_results(self, batch_id: str) -> list[dict]:  # returns results

class OpenAIProvider(LLMProvider):
    # Implement using OpenAI Batch API
    # Model: gpt-4o
    
# Future:
# class AnthropicProvider(LLMProvider): ...
# class GeminiProvider(LLMProvider): ...
```

Store the provider choice and model name in environment variables:
```
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
```

---

## 5. Report Tree Structure

### Three-Layer Design

The report is a JSON tree. Each node has:
```json
{
  "id": "c1",
  "title": "Criterion 1: Unrestricted Intellectual Scope",
  "summary": "2-3 sentence verdict for this section",
  "satisfaction_pct": 65,
  "children": [
    {
      "id": "c1.1",
      "title": "Benchmark Performance Trajectory",
      "summary": "Paragraph-length evidence cluster",
      "children": [
        {
          "id": "c1.1.1",
          "title": "GPQA Diamond scores",
          "detail": "Detailed evidence with specific numbers",
          "references": [
            {"source": "OpenAI blog", "url": "...", "date": "2025-12-15", "weight": 4}
          ]
        }
      ]
    }
  ]
}
```

### Top-Level Structure (Layer 1)

The report tree has these top-level nodes:

1. **Executive Summary** — overall scenario assessment (which scenario from A-E best describes current AI), 3-4 sentences
2. **Criterion 1: Unrestricted Intellectual Scope** — assessment + satisfaction percentage
3. **Criterion 2: Generative Causal World and Self Model** — assessment + satisfaction percentage
4. **Criterion 3: Autonomous Goal Decomposition** — assessment + satisfaction percentage
5. **Criterion 4: Self-Directed Learning** — assessment + satisfaction percentage
6. **Criterion 5: Epistemological Meta-Reasoning** — assessment + satisfaction percentage
7. **Cross-Criterion Analysis** — interdependencies, what the pattern reveals

Each criterion node (2-6) contains 3-5 Layer 2 evidence clusters. Each evidence cluster contains 2-4 Layer 3 detailed evidence items with references.

### HTML Rendering

Generate a static HTML page from the report tree JSON:
- Layer 1: Always visible, clean typography
- Layer 2: Hidden by default, revealed by clicking/tapping a Layer 1 section
- Layer 3: Hidden by default, revealed by clicking/tapping a Layer 2 section
- Use vanilla HTML/CSS/JS — no frameworks needed
- Include the report generation date and list of sources consulted
- Include a "methodology" section at the bottom explaining the five-criteria framework briefly

The HTML file should be self-contained (all CSS/JS inline) for easy hosting on GitHub Pages.

---

## 6. The AGI Evaluation Framework

This is the analytical framework that drives all LLM analysis. It must be included in full as the system prompt for both Wave 1 and Wave 2 API calls.

**IMPORTANT: The framework document is stored at `framework/agi_evaluation_framework.md` in this repository.** Claude Code must read this file and use its contents as the system prompt. Do NOT summarise or truncate it — the full document is required for accurate evaluation.

The framework defines:
- Five criteria for AGI (Unrestricted Intellectual Scope, Generative Causal World Model, Autonomous Goal Decomposition, Self-Directed Learning, Epistemological Meta-Reasoning)
- Dependency structure between criteria
- Five scenarios (A through E) from current state to true AGI
- Per-criterion evaluation guides: what constitutes genuine vs. superficial progress
- Failure signatures to watch for

**When the system is first set up, copy the framework document from the project knowledge into `framework/agi_evaluation_framework.md`.** This is the document titled "Artificial General Intelligence (AGI) — Evaluation Framework" that defines the five criteria, five scenarios, and all evaluation guidance.

---

## 7. Scheduling (GitHub Actions)

### Workflow 1: Daily Fetch
```yaml
name: Daily Fetch
on:
  schedule:
    - cron: '0 6 * * *'  # 06:00 UTC daily
  workflow_dispatch:  # manual trigger

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
      - run: python src/fetch/main.py
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          SEMANTIC_SCHOLAR_API_KEY: ${{ secrets.SEMANTIC_SCHOLAR_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
```

### Workflow 2: Report Generation
```yaml
name: Generate Report
on:
  schedule:
    - cron: '0 8 */3 * *'  # 08:00 UTC every 3 days
  workflow_dispatch:  # manual trigger

jobs:
  process:
    runs-on: ubuntu-latest
    timeout-minutes: 120  # Batch API may take time
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: python src/process/main.py
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          LLM_PROVIDER: openai
          LLM_MODEL: gpt-4o
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
      - run: python src/report/generate_html.py
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./output
```

---

## 8. Telegram Notifications

Use the Telegram Bot API: `POST https://api.telegram.org/bot{token}/sendMessage`

### Notification Types

**1. Fetch summary (after daily fetch completes):**
```
📥 Fetch cycle: {date} {time} UTC
✅ {n_success}/{n_total} sources OK
⚠️ {source}: {warning_reason}
❌ {source}: {error_reason}
New items: {total} ({breakdown by category})
```

**2. Data refresh detected (when high-weight source publishes significant content):**
```
🔔 High-signal update detected
Source: {name} (weight {n})
Title: "{title}"
```
Trigger this when a weight-4 or weight-5 source publishes new content.

**3. Wave 1 summary (after Wave 1 processing completes):**
```
🔬 Wave 1 complete: {date}
Sources processed: {n_items} items from {n_sources} sources
Claims extracted: {n_claims}
By criterion: C1:{n} | C2:{n} | C3:{n} | C4:{n} | C5:{n}
Batch API cost: ${cost}
Duration: {minutes} min
```

**4. Wave 2 summary (after report generation completes):**
```
📊 Report generated: {date}
Scenario assessment: {scenario}
Report URL: {github_pages_url}
Batch API cost: ${cost}
Duration: {minutes} min
```

**On any failure:** Replace the summary with an error notification including the step that failed and the error message.

---

## 9. Environment Variables

All credentials and configuration stored in `.env` (local) or GitHub Actions Secrets (production):

```
# Database
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require

# LLM
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-...

# Telegram
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

# Source-specific auth
SEMANTIC_SCHOLAR_API_KEY=...
OPENREVIEW_USERNAME=...
OPENREVIEW_PASSWORD=...
GITHUB_TOKEN=...  # for GitHub API rate limits

# Configuration
REPORT_INTERVAL_DAYS=3
FETCH_SCHEDULE_UTC=0600
```

Create a `.env.example` with all variables listed (values blank) and add `.env` to `.gitignore`.

---

## 10. Project Structure

```
agi-tracker/
├── .github/
│   └── workflows/
│       ├── fetch.yml
│       └── report.yml
├── framework/
│   └── agi_evaluation_framework.md    # The full analytical framework
├── src/
│   ├── fetch/
│   │   ├── main.py                    # Orchestrates all fetchers
│   │   ├── rss_fetcher.py             # RSS/Atom feed fetcher
│   │   ├── api_fetcher.py             # REST API fetcher (Semantic Scholar, GitHub, HF)
│   │   ├── csv_fetcher.py             # CSV download fetcher (Epoch AI)
│   │   ├── graphql_fetcher.py         # GraphQL fetcher (LessWrong)
│   │   ├── openreview_fetcher.py      # OpenReview SDK fetcher
│   │   └── scrape_fetcher.py          # Web scraping fetcher (ARC-AGI, AISI)
│   ├── process/
│   │   ├── main.py                    # Orchestrates Wave 1 → Wave 2
│   │   ├── wave1.py                   # Wave 1: source-level analysis
│   │   ├── wave2.py                   # Wave 2: synthesis and tree generation
│   │   └── prompts.py                 # Prompt templates for Wave 1 and Wave 2
│   ├── llm/
│   │   ├── provider.py                # Abstract LLMProvider base class
│   │   └── openai_provider.py         # OpenAI Batch API implementation
│   ├── report/
│   │   ├── generate_html.py           # Convert report tree JSON to static HTML
│   │   └── template.html              # HTML template with expandable sections
│   ├── notify/
│   │   └── telegram.py                # Telegram notification functions
│   ├── db/
│   │   ├── connection.py              # Database connection management
│   │   ├── models.py                  # Database operations (insert, query, deduplicate)
│   │   └── migrations/
│   │       └── 001_initial_schema.sql # The schema from Section 3
│   └── config.py                      # Environment variable loading and validation
├── output/                            # Generated HTML reports (deployed to GitHub Pages)
│   └── index.html
├── tests/                             # Basic tests for critical paths
│   ├── test_fetchers.py
│   ├── test_wave1.py
│   └── test_report.py
├── .env.example
├── .gitignore
├── requirements.txt
├── TECHNICAL.md                       # Auto-generated technical documentation (see Section 11)
├── README.md                          # Project overview for public audience
└── SPEC.md                            # This file
```

---

## 11. TECHNICAL.md Requirements

**This is critical.** Claude Code must create and maintain a `TECHNICAL.md` file that documents every relevant technical detail of the project. This document must be **factually accurate** — it describes what the system actually does, not what it aspirationally should do. If the implementation differs from this spec (which is normal), TECHNICAL.md reflects the implementation, not the spec.

TECHNICAL.md must include:

1. **System architecture diagram** (ASCII or Mermaid) showing the data flow from sources → Neon → LLM → report → GitHub Pages
2. **Database schema** — the actual SQL that was executed, including any changes from the spec
3. **Source registry** — every source with its actual fetch method, URL, auth requirements, and any quirks discovered during implementation
4. **API integrations** — for each external API, document: the endpoint used, auth method, rate limits respected, response format expected, and error handling approach
5. **LLM prompt architecture** — the actual prompt templates used for Wave 1 and Wave 2, including the system prompt structure and how the framework document is incorporated
6. **Report tree schema** — the actual JSON schema of the report tree, with an example
7. **GitHub Actions workflows** — what each workflow does, what triggers it, what secrets it needs
8. **Telegram notification format** — actual message templates
9. **Environment variables** — complete list with descriptions (no values)
10. **Known limitations and quirks** — anything discovered during implementation that a future developer should know
11. **Cost estimates** — estimated per-cycle costs for API calls based on actual token usage observed during testing

**Update TECHNICAL.md every time the implementation changes.** It must always reflect the current state of the code.

---

## 12. Implementation Notes

### Error Handling
- Every fetch source should be wrapped in try/catch. One source failing must not prevent others from completing.
- Log all errors to `fetch_logs` table with the specific error message.
- Implement exponential backoff for transient API failures (timeouts, rate limits).
- If a source fails 3 consecutive fetch cycles, flag it in the Telegram notification but keep trying.

### Deduplication
- Primary deduplication key: `(source_id, external_id)` where external_id is the URL, DOI, or unique identifier from the source.
- For RSS feeds, the item link/guid is the external_id.
- For API results, use the source's native ID (paper ID, repo ID, etc.).

### Rate Limiting
- arXiv: 3-second delay between requests
- Semantic Scholar: 1 request per second (authenticated)
- GitHub API: 5,000 requests/hour (authenticated), 30/minute for search
- All others: 1-second delay between requests as a safe default

### Testing
- Write basic integration tests that verify each fetcher can connect and parse a response.
- Write a test that verifies the Wave 1 prompt template produces valid JSON output.
- Write a test that verifies the HTML generator produces a valid page from sample report JSON.
- Tests should be runnable locally and in GitHub Actions.

### Git Practices
- `.gitignore` must include: `.env`, `__pycache__/`, `*.pyc`, `output/` (generated, not tracked), `.venv/`
- The `output/` directory is deployed by the GitHub Actions workflow to the `gh-pages` branch, not committed to main.

---

## 13. Getting Started Checklist (For the Developer)

After Claude Code finishes implementation, the developer needs to:

1. [ ] Create a Neon project at neon.tech and get the connection string
2. [ ] Create an OpenAI API key at platform.openai.com
3. [ ] Create a Telegram bot via @BotFather and get the bot token
4. [ ] Get your Telegram chat ID (message @userinfobot)
5. [ ] Optionally: get a Semantic Scholar API key at semanticscholar.org/product/api
6. [ ] Optionally: create an OpenReview account at openreview.net
7. [ ] Add all credentials as GitHub Actions secrets in the repo settings
8. [ ] Run the database migration: `psql $DATABASE_URL -f src/db/migrations/001_initial_schema.sql`
9. [ ] Seed the sources table: `python src/db/seed_sources.py`
10. [ ] Test locally: `python src/fetch/main.py` then `python src/process/main.py`
11. [ ] Enable GitHub Pages (Settings → Pages → Source: Deploy from branch → gh-pages)
12. [ ] Verify GitHub Actions workflows are enabled
13. [ ] Copy the AGI evaluation framework document into `framework/agi_evaluation_framework.md`
