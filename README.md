# AGI Capability Tracker

Automated system that tracks progress toward Artificial General Intelligence (AGI) by monitoring 20 curated AI research sources daily, analysing them against a rigorous five-criterion framework, and producing a public report every three days.

## What It Does

1. **Fetches** content daily from 20 sources: arXiv, Semantic Scholar, OpenReview, OpenAI/DeepMind/Anthropic/Meta blogs, ARC-AGI leaderboard, Epoch AI datasets, SWE-bench, HuggingFace leaderboard, LessWrong, newsletters, and the UK AI Safety Institute.
2. **Analyses** fetched content using a two-wave LLM pipeline (OpenAI GPT-4o Batch API):
   - **Wave 1:** Extracts and weights specific claims from each source, mapping them to one of the five AGI criteria.
   - **Wave 2:** Synthesises all weighted claims into a structured report tree assessing where current AI systems stand.
3. **Publishes** a self-contained HTML report to GitHub Pages, updated every 3 days.
4. **Notifies** via Telegram at each pipeline step.

## The Five AGI Criteria

Based on the [AGI Evaluation Framework](framework/agi_evaluation_framework.md):

| # | Criterion | What It Means |
|---|-----------|--------------|
| 1 | Unrestricted Intellectual Scope | Reasoning across all domains with no architectural performance ceiling |
| 2 | Generative Causal World and Self Model | Causal-first world model capable of genuine counterfactual simulation |
| 3 | Autonomous Goal Decomposition | Multi-step planning, obstacle handling, and strategy revision without human re-prompting |
| 4 | Self-Directed Learning | Identifies own knowledge gaps and pursues resolution autonomously |
| 5 | Epistemological Meta-Reasoning | Understands *why* certain kinds of reasoning are reliable; prefers first-principles over statistical inference |

AGI requires all five criteria to be satisfied simultaneously.

## Architecture

```
GitHub Actions (daily)         GitHub Actions (every 3 days)
  fetch.yml                       report.yml
     │                               │
     ▼                               ▼
src/fetch/main.py           src/process/main.py
(20 fetchers)               Wave 1 → Wave 2 → HTML
     │                               │
     └──────── Neon PostgreSQL ───────┘
                                     │
                             output/index.html → GitHub Pages
                             Telegram notifications
```

## Setup

### Prerequisites
- Python 3.12+
- [Neon](https://neon.tech) account (PostgreSQL, free tier)
- OpenAI API key
- Telegram bot (optional but recommended)

### Steps

1. **Clone and install:**
   ```bash
   git clone https://github.com/your-username/dont-panic
   cd dont-panic
   pip install -r requirements.txt
   ```

2. **Configure credentials:**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

3. **Initialize the database:**
   ```bash
   psql $DATABASE_URL -f src/db/migrations/001_initial_schema.sql
   python src/db/seed_sources.py
   ```

4. **Test locally:**
   ```bash
   python src/fetch/main.py      # Fetch all sources
   python src/process/main.py    # Run Wave 1 + Wave 2
   python src/report/generate_html.py  # Generate HTML
   ```

5. **Add GitHub Actions secrets** (Settings → Secrets → Actions):
   - `DATABASE_URL`
   - `OPENAI_API_KEY`
   - `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`
   - `SEMANTIC_SCHOLAR_API_KEY` (optional)
   - `GH_API_TOKEN` (optional, for GitHub API rate limits)
   - `OPENREVIEW_USERNAME` + `OPENREVIEW_PASSWORD` (optional)

6. **Enable GitHub Pages** (Settings → Pages → Source: Deploy from branch → `gh-pages`)

7. **Enable GitHub Actions** workflows are enabled by default.

## Tech Stack

- **Language:** Python 3.12
- **Database:** Neon PostgreSQL (`psycopg2`)
- **LLM:** OpenAI GPT-4o via Batch API (50% cost reduction)
- **Fetching:** `feedparser`, `requests`, `beautifulsoup4`, `pandas`
- **CI/CD:** GitHub Actions
- **Hosting:** GitHub Pages (static HTML)
- **Notifications:** Telegram Bot API

## Cost

Estimated **~$0.30–$0.50 per report cycle** (every 3 days) using the OpenAI Batch API. Monthly cost ~$3–5.

## Live Report

Available at: `https://your-username.github.io/dont-panic/`

---

*Built to track the five criteria that separate genuine AGI from advanced narrow AI.*
