"""Configuration and environment variable loading."""
import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class Config:
    # Database
    database_url: str

    # LLM
    llm_provider: str
    llm_model: str
    openai_api_key: str

    # Telegram
    telegram_bot_token: str
    telegram_chat_id: str

    # Source-specific auth (optional)
    semantic_scholar_api_key: str
    openreview_username: str
    openreview_password: str
    github_token: str

    # Configuration
    report_interval_days: int
    fetch_schedule_utc: str

    @classmethod
    def from_env(cls) -> "Config":
        """Load config from environment variables. Raises ValueError for missing required vars."""
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise ValueError("Required environment variable DATABASE_URL is not set")

        return cls(
            database_url=database_url,
            llm_provider=os.environ.get("LLM_PROVIDER", "openai"),
            llm_model=os.environ.get("LLM_MODEL", "gpt-4o"),
            openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
            telegram_bot_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.environ.get("TELEGRAM_CHAT_ID", ""),
            semantic_scholar_api_key=os.environ.get("SEMANTIC_SCHOLAR_API_KEY", ""),
            openreview_username=os.environ.get("OPENREVIEW_USERNAME", ""),
            openreview_password=os.environ.get("OPENREVIEW_PASSWORD", ""),
            github_token=os.environ.get("GITHUB_TOKEN", ""),
            report_interval_days=int(os.environ.get("REPORT_INTERVAL_DAYS", "3")),
            fetch_schedule_utc=os.environ.get("FETCH_SCHEDULE_UTC", "0600"),
        )


_config: "Config | None" = None


def get_config() -> Config:
    """Lazily initialize and return the cached Config instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config
