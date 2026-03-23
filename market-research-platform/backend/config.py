# filepath: market-research-platform/backend/config.py
# Application configuration using Pydantic Settings.
# All values are read from environment variables (or .env file).
# Import `settings` anywhere in the app: from config import settings

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── LLM Provider ("gemini" or "openai") ─────────────────────────────
    llm_provider: str = "gemini"

    # ── Gemini ──────────────────────────────────────────────────────────
    gemini_api_key: str = ""
    gemini_llm_model: str = "models/gemini-2.0-flash"
    gemini_embedding_model: str = "models/gemini-embedding-001"

    # ── OpenAI ──────────────────────────────────────────────────────────
    openai_api_key: str = ""
    openai_llm_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    # ── LlamaParse ────────────────────────────────────────────────────────
    llama_cloud_api_key: str = ""  # Optional — falls back to unstructured.io

    # ── PostgreSQL ────────────────────────────────────────────────────────
    postgres_user: str = "mrip"
    postgres_password: str = "mrip_secret"
    postgres_db: str = "market_research"
    postgres_host: str = "db"
    postgres_port: int = 5432

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        """Sync URL used by LlamaIndex PGVectorStore initialization."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── News APIs ─────────────────────────────────────────────────────────
    newsapi_key: str = ""
    news_topics: str = "supply chain, AI, logistics, market trends"
    news_sync_interval_minutes: int = 60

    # ── Scheduler ─────────────────────────────────────────────────────────
    weekly_brief_cron: str = "0 8 * * 1"  # Monday 8am

    # ── App ───────────────────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "INFO"
    upload_dir: str = "/app/uploads"
    max_upload_size_mb: int = 50

    # ── LlamaIndex chunking defaults ──────────────────────────────────────
    chunk_size: int = 512
    chunk_overlap: int = 128
    retrieval_top_k: int = 5


# Singleton settings instance
settings = Settings()
