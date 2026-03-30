"""
Seed the sources table with all 20 data sources.
Idempotent — skips sources that already exist by name.
Run: python src/db/seed_sources.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db.connection import execute_query, execute_returning

SOURCES = [
    # (name, category, fetch_method, url, weight_default)
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


def seed():
    existing = {row["name"] for row in execute_query("SELECT name FROM sources")}
    inserted = 0
    skipped = 0
    for name, category, fetch_method, url, weight_default in SOURCES:
        if name in existing:
            print(f"  skip (exists): {name}")
            skipped += 1
            continue
        sql = """
            INSERT INTO sources (name, category, fetch_method, url, weight_default)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        source_id = execute_returning(sql, (name, category, fetch_method, url, weight_default))
        print(f"  inserted id={source_id}: {name}")
        inserted += 1
    print(f"\nDone: {inserted} inserted, {skipped} skipped.")


if __name__ == "__main__":
    seed()
