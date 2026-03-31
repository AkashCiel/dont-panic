"""
Seed the sources table: 20 cognitive sources + 12 diffusion sources (ids 21–32).
Idempotent — uses insert_source for cognitive rows and upserts diffusion rows by id.

Requires migration 002 (track column). Run: python src/db/seed_sources.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db.connection import execute_non_query
from src.db.models import insert_source

# (name, category, fetch_method, url, weight_default) — track = cognitive
COGNITIVE_SOURCES = [
    ("arXiv cs.AI", "Papers", "rss", "https://arxiv.org/rss/cs.AI", 4),
    ("arXiv cs.LG", "Papers", "rss", "https://arxiv.org/rss/cs.LG", 4),
    ("arXiv cs.CL", "Papers", "rss", "https://arxiv.org/rss/cs.CL", 4),
    ("Semantic Scholar", "Papers", "rest_api", "https://api.semanticscholar.org/graph/v1/paper/search", 5),
    ("OpenReview", "Papers", "sdk", "https://openreview.net", 5),
    ("Epoch AI datasets", "Quantitative", "csv", "https://epoch.ai/data/ai-models", 5),
    ("OpenAI blog", "Lab blog", "rss", "https://openai.com/news/rss.xml", 4),
    ("Google DeepMind blog", "Lab blog", "rss", "https://deepmind.google/blog/rss.xml", 4),
    (
        "Anthropic research",
        "Lab blog",
        "rss",
        "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml",
        4,
    ),
    ("Meta AI (FAIR)", "Lab blog", "rss", "https://research.facebook.com/feed/", 4),
    ("DeepSeek releases", "Lab releases", "rest_api", "https://api.github.com/orgs/deepseek-ai/repos", 3),
    ("ARC-AGI leaderboard", "Benchmark", "scrape", "https://arcprize.org/leaderboard", 5),
    ("Epoch AI Benchmarking Hub", "Benchmark", "csv", "https://epoch.ai/benchmarks", 5),
    (
        "HuggingFace Open LLM Leaderboard",
        "Benchmark",
        "rest_api",
        "https://huggingface.co/api/models",
        2,
    ),
    ("SWE-bench", "Benchmark", "scrape", "https://github.com/SWE-bench/swe-bench.github.io", 2),
    ("Import AI newsletter", "Newsletter", "rss", "https://importai.substack.com/feed", 3),
    ("Interconnects newsletter", "Newsletter", "rss", "https://www.interconnects.ai/feed", 3),
    ("Zvi Mowshowitz AI roundup", "Newsletter", "rss", "https://thezvi.substack.com/feed", 3),
    ("UK AI Safety Institute", "Institutional", "scrape", "https://www.aisi.gov.uk/research", 2),
    ("LessWrong", "Community", "graphql", "https://www.lesswrong.com/graphql", 1),
]

# (id, name, category, fetch_method, url, weight_default) — track = diffusion
DIFFUSION_SOURCES = [
    (
        21,
        "SEC EDGAR Full-Text Search",
        "Financial",
        "sec_edgar",
        "https://efts.sec.gov/LATEST/search-index?q=%22artificial+intelligence%22&dateRange=custom&startdt={start}&enddt={end}&forms=10-K,10-Q,8-K",
        5,
    ),
    (
        22,
        "Epoch AI Company Revenue",
        "Financial",
        "csv",
        "https://epoch.ai/data/ai_companies_revenue_reports.csv",
        5,
    ),
    (
        23,
        "SAM.gov Federal Procurement",
        "Government",
        "sam_gov",
        "https://api.sam.gov/prod/opportunities/v2/search",
        5,
    ),
    (
        24,
        "USAspending.gov",
        "Government",
        "usaspending",
        "https://api.usaspending.gov/api/v2/search/spending_by_award/",
        5,
    ),
    (
        25,
        "TED EU Procurement",
        "Government",
        "ted_eu",
        "https://api.ted.europa.eu/v3/notices/search",
        4,
    ),
    (
        26,
        "Cloudflare Radar AI Insights",
        "Usage Metrics",
        "cloudflare_radar",
        "https://api.cloudflare.com/client/v4/radar/ai/",
        3,
    ),
    (27, "AWS AI Blog", "Cloud Provider", "rss_ai", "https://aws.amazon.com/blogs/machine-learning/feed/", 4),
    (
        28,
        "Azure AI Blog",
        "Cloud Provider",
        "rss_ai",
        "https://techcommunity.microsoft.com/t5/ai-azure-ai-services-blog/bg-p/Azure-AI-Services-blog/rss",
        4,
    ),
    (29, "Google Cloud AI Blog", "Cloud Provider", "rss_ai", "https://cloud.google.com/feeds/cloud-blog.xml", 4),
    (30, "TechCrunch AI", "News", "rss_ai", "https://techcrunch.com/category/artificial-intelligence/feed/", 3),
    (31, "VentureBeat AI", "News", "rss_ai", "https://venturebeat.com/category/ai/feed/", 3),
    (
        32,
        "Anthropic Economic Index",
        "Usage Metrics",
        "economic_index",
        "https://www.anthropic.com/research/economic-index-geography",
        3,
    ),
]

DIFFUSION_UPSERT_SQL = """
INSERT INTO sources (id, name, category, fetch_method, url, weight_default, track)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    fetch_method = EXCLUDED.fetch_method,
    url = EXCLUDED.url,
    weight_default = EXCLUDED.weight_default,
    track = EXCLUDED.track
"""


def _sync_sources_id_sequence() -> None:
    execute_non_query(
        "SELECT setval(pg_get_serial_sequence('sources', 'id'), "
        "(SELECT COALESCE(MAX(id), 1) FROM sources))"
    )


def seed() -> None:
    for name, category, fetch_method, url, weight_default in COGNITIVE_SOURCES:
        sid = insert_source(name, category, fetch_method, url, weight_default, track="cognitive")
        print(f"  cognitive id={sid}: {name}")

    for row in DIFFUSION_SOURCES:
        sid, name, category, fetch_method, url, weight_default = row
        execute_non_query(
            DIFFUSION_UPSERT_SQL,
            (sid, name, category, fetch_method, url, weight_default, "diffusion"),
        )
        print(f"  diffusion upsert id={sid}: {name}")

    _sync_sources_id_sequence()
    print("\nDone: cognitive sources ensured; diffusion sources 21–32 upserted; sequence synced.")


if __name__ == "__main__":
    seed()
